"""Kafka connector — produce/consume with a non-blocking circuit breaker.

Registered as ``type: kafka`` in dex.yaml sources.  Backed by
``confluent-kafka`` (librdkafka).  Kafka being slow or down must never
block or crash the pipeline request path:

- Produce is fire-and-forget into a small bounded local buffer; broker
  errors are caught, logged, and swallowed (never raised).
- Consume returns ``[]`` on broker errors instead of raising.
- ``health_check`` returns ``False`` (never raises) on any failure.

Example dex.yaml::

    sources:
      movie_changes_producer:
        type: kafka
        connection:
          bootstrap_servers: "kafka:9092"
          topic: movie-changes
          mode: produce

      movie_changes_consumer:
        type: kafka
        connection:
          bootstrap_servers: "kafka:9092"
          topic: movie-changes
          mode: consume
          group_id: movie-changes-consumer
"""

from __future__ import annotations

import json
from collections import deque
from typing import Any

import structlog
from confluent_kafka import Consumer, KafkaException, Producer
from confluent_kafka.admin import AdminClient

from dataenginex.core.interfaces import BaseConnector
from dataenginex.data.connectors import connector_registry

logger = structlog.get_logger()


@connector_registry.decorator("kafka")
class KafkaConnector(BaseConnector):
    """Produce/consume connector backed by confluent-kafka.

    Args:
        bootstrap_servers: Kafka broker list (e.g. ``"kafka:9092"``).
        topic: Topic to produce to or consume from.
        mode: ``"produce"`` or ``"consume"``.
        group_id: Consumer group ID — required when ``mode="consume"``.
        timeout_seconds: Timeout for broker calls (poll, metadata, flush).
        max_buffer: Cap on the local fire-and-forget produce buffer. When
            full, the oldest pending record is dropped (never blocks).
    """

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        mode: str,
        group_id: str | None = None,
        timeout_seconds: float = 10.0,
        max_buffer: int = 1000,
        **kwargs: Any,
    ) -> None:
        if mode not in ("produce", "consume"):
            msg = f"KafkaConnector mode must be 'produce' or 'consume', got {mode!r}"
            raise ValueError(msg)
        if mode == "consume" and not group_id:
            msg = "KafkaConnector requires group_id when mode='consume'"
            raise ValueError(msg)

        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._mode = mode
        self._group_id = group_id
        self._timeout = timeout_seconds
        self._max_buffer = max_buffer
        self._buffer: deque[dict[str, Any]] = deque()
        self._producer: Producer | None = None
        self._consumer: Consumer | None = None

    def connect(self) -> None:
        if self._mode == "produce":
            self._producer = Producer({"bootstrap.servers": self._bootstrap_servers})
        else:
            self._consumer = Consumer(
                {
                    "bootstrap.servers": self._bootstrap_servers,
                    "group.id": self._group_id,
                    "auto.offset.reset": "latest",
                }
            )
            self._consumer.subscribe([self._topic])
        logger.debug("kafka connector ready", topic=self._topic, mode=self._mode)

    def disconnect(self) -> None:
        if self._producer is not None:
            try:
                self._producer.flush(self._timeout)
            except Exception as exc:  # noqa: BLE001 - never crash on shutdown
                logger.warning("kafka producer flush failed", error=str(exc))
            self._producer = None
        if self._consumer is not None:
            try:
                self._consumer.close()
            except Exception as exc:  # noqa: BLE001
                logger.warning("kafka consumer close failed", error=str(exc))
            self._consumer = None

    def write(self, data: Any, *, table: str = "", **kwargs: Any) -> None:
        """Fire-and-forget produce. Never blocks or raises on broker errors."""
        if self._mode != "produce":
            raise NotImplementedError("KafkaConnector is consume-only in mode='consume'")
        if self._producer is None:
            msg = "KafkaConnector not connected — call connect() first"
            raise RuntimeError(msg)

        records = data if isinstance(data, list) else [data]

        for record in records:
            if len(self._buffer) >= self._max_buffer:
                dropped = self._buffer.popleft()
                logger.warning(
                    "kafka connector local buffer full, dropping oldest record",
                    topic=self._topic,
                    dropped=dropped,
                )
            self._buffer.append(record)

            try:
                self._producer.produce(self._topic, value=json.dumps(record).encode("utf-8"))
                self._producer.poll(0)  # trigger delivery callbacks, non-blocking
                self._buffer.popleft()
            except (KafkaException, BufferError, Exception) as exc:  # noqa: BLE001
                # Circuit breaker: broker down/slow must never crash the caller.
                logger.error(
                    "kafka connector produce failed, record kept in local buffer",
                    topic=self._topic,
                    error=str(exc),
                )

    def read(self, *, table: str | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        """Poll available messages for up to timeout_seconds. Never raises on broker errors."""
        if self._mode != "consume":
            raise NotImplementedError("KafkaConnector is produce-only in mode='produce'")
        if self._consumer is None:
            msg = "KafkaConnector not connected — call connect() first"
            raise RuntimeError(msg)

        records: list[dict[str, Any]] = []
        try:
            msgs = self._consumer.consume(num_messages=500, timeout=self._timeout)
            for kafka_msg in msgs:
                if kafka_msg.error():
                    logger.error("kafka connector consume error", error=str(kafka_msg.error()))
                    continue
                try:
                    val = kafka_msg.value()
                    if val is None:
                        continue  # tombstone
                    records.append(json.loads(val.decode("utf-8")))
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    logger.warning("kafka connector dropped unparseable message", error=str(exc))
        except Exception as exc:  # noqa: BLE001 - broker down must return [] not raise
            logger.error("kafka connector broker unreachable", topic=self._topic, error=str(exc))
            return []

        logger.debug("kafka connector read complete", topic=self._topic, records=len(records))
        return records

    def health_check(self) -> bool:
        try:
            client = AdminClient({"bootstrap.servers": self._bootstrap_servers})
            metadata = client.list_topics(timeout=self._timeout)
            return metadata is not None
        except Exception:
            return False
