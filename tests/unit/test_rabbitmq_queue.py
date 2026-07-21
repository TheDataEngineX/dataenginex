"""Tests for RabbitMQQueue — all pika connections/channels are mocked.

No real RabbitMQ broker required.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

from dataenginex.orchestration.queue.rabbitmq import RabbitMQQueue


def _make_channel_mock() -> MagicMock:
    channel = MagicMock()
    channel.basic_get.return_value = (None, None, None)
    return channel


def _patched_connection(channel: MagicMock) -> MagicMock:
    connection = MagicMock()
    connection.channel.return_value = channel
    return connection


class TestPublish:
    def test_successful_publish_serializes_and_sends(self) -> None:
        channel = _make_channel_mock()
        connection = _patched_connection(channel)

        with patch("pika.BlockingConnection", return_value=connection):
            queue = RabbitMQQueue(host="localhost", queue_name="jobs")
            queue.publish({"movie_id": 42})

        assert channel.basic_publish.called
        kwargs = channel.basic_publish.call_args.kwargs
        assert kwargs["routing_key"] == "jobs"
        assert json.loads(kwargs["body"]) == {"movie_id": 42}

    def test_priority_passed_through_to_publish(self) -> None:
        channel = _make_channel_mock()
        connection = _patched_connection(channel)

        with patch("pika.BlockingConnection", return_value=connection):
            queue = RabbitMQQueue(host="localhost", queue_name="jobs")
            queue.publish({"movie_id": 42}, priority=7)

        kwargs = channel.basic_publish.call_args.kwargs
        assert kwargs["properties"].priority == 7

    def test_broker_down_publish_does_not_raise(self) -> None:
        with patch("pika.BlockingConnection", side_effect=ConnectionError("no broker")):
            queue = RabbitMQQueue(host="localhost", queue_name="jobs")
            queue.publish({"movie_id": 42})  # must not raise


class TestConsume:
    def test_successful_consume_acks_message(self) -> None:
        channel = _make_channel_mock()
        method = MagicMock(delivery_tag=1)
        body = json.dumps({"movie_id": 42}).encode("utf-8")
        channel.basic_get.side_effect = [(method, None, body), (None, None, None)]
        connection = _patched_connection(channel)

        handler_calls: list[dict[str, Any]] = []

        def handler(msg: dict[str, Any]) -> bool:
            handler_calls.append(msg)
            return True

        with patch("pika.BlockingConnection", return_value=connection):
            queue = RabbitMQQueue(host="localhost", queue_name="jobs")
            processed = queue.consume(handler)

        assert processed == 1
        assert handler_calls == [{"movie_id": 42}]
        channel.basic_ack.assert_called_once_with(delivery_tag=1)
        channel.basic_nack.assert_not_called()

    def test_handler_failure_nacks_with_requeue_when_no_dlq(self) -> None:
        channel = _make_channel_mock()
        method = MagicMock(delivery_tag=1)
        body = json.dumps({"movie_id": 42}).encode("utf-8")
        channel.basic_get.side_effect = [(method, None, body), (None, None, None)]
        connection = _patched_connection(channel)

        with patch("pika.BlockingConnection", return_value=connection):
            queue = RabbitMQQueue(host="localhost", queue_name="jobs")  # no dlq_name
            queue.consume(lambda msg: False)

        channel.basic_ack.assert_not_called()
        channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=True)

    def test_handler_failure_routes_to_dlq_without_requeue_when_dlq_configured(self) -> None:
        channel = _make_channel_mock()
        method = MagicMock(delivery_tag=1)
        body = json.dumps({"movie_id": 42}).encode("utf-8")
        channel.basic_get.side_effect = [(method, None, body), (None, None, None)]
        connection = _patched_connection(channel)

        with patch("pika.BlockingConnection", return_value=connection):
            queue = RabbitMQQueue(host="localhost", queue_name="jobs", dlq_name="jobs.dlq")
            queue.consume(lambda msg: False)

        channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)

    def test_handler_exception_is_treated_as_failure(self) -> None:
        channel = _make_channel_mock()
        method = MagicMock(delivery_tag=1)
        body = json.dumps({"movie_id": 42}).encode("utf-8")
        channel.basic_get.side_effect = [(method, None, body), (None, None, None)]
        connection = _patched_connection(channel)

        def handler(msg: dict[str, Any]) -> bool:
            raise RuntimeError("boom")

        with patch("pika.BlockingConnection", return_value=connection):
            queue = RabbitMQQueue(host="localhost", queue_name="jobs")
            processed = queue.consume(handler)

        assert processed == 1
        channel.basic_ack.assert_not_called()
        channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=True)

    def test_broker_down_consume_does_not_raise(self) -> None:
        with patch("pika.BlockingConnection", side_effect=ConnectionError("no broker")):
            queue = RabbitMQQueue(host="localhost", queue_name="jobs")
            processed = queue.consume(lambda msg: True)  # must not raise

        assert processed == 0

    def test_prefetch_count_bounds_number_of_messages_pulled(self) -> None:
        """Fault-injection-style bound check: 5 messages available, prefetch_count=3.

        This asserts basic_get is called exactly 3 times (the bound), not
        merely "at least 1" — a wrong implementation that ignores
        prefetch_count and drains the whole queue (5 calls + the trailing
        empty check) would fail this assertion, proving it's a real check.
        """
        channel = _make_channel_mock()
        messages = [
            (MagicMock(delivery_tag=i), None, json.dumps({"movie_id": i}).encode("utf-8"))
            for i in range(5)
        ]
        channel.basic_get.side_effect = messages
        connection = _patched_connection(channel)

        with patch("pika.BlockingConnection", return_value=connection):
            queue = RabbitMQQueue(host="localhost", queue_name="jobs", prefetch_count=3)
            processed = queue.consume(lambda msg: True)

        assert processed == 3
        assert channel.basic_get.call_count == 3


class TestHealthCheck:
    def test_health_check_true_on_success(self) -> None:
        channel = _make_channel_mock()
        connection = _patched_connection(channel)
        with patch("pika.BlockingConnection", return_value=connection):
            queue = RabbitMQQueue(host="localhost", queue_name="jobs")
            assert queue.health_check() is True

    def test_health_check_false_on_failure(self) -> None:
        with patch("pika.BlockingConnection", side_effect=ConnectionError("no broker")):
            queue = RabbitMQQueue(host="localhost", queue_name="jobs")
            assert queue.health_check() is False


if __name__ == "__main__":
    # ponytail: minimal smoke self-check, in addition to the pytest suite above
    with patch("pika.BlockingConnection", side_effect=ConnectionError("no broker")):
        q = RabbitMQQueue(host="localhost", queue_name="jobs")
        q.publish({"movie_id": 1})  # must not raise
        assert q.consume(lambda m: True) == 0
        assert q.health_check() is False
    print("rabbitmq queue self-check passed")
