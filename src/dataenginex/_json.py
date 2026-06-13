"""orjson-backed JSON helpers — drop-in replacement for stdlib json.

All call sites should use these instead of ``import json`` directly.
"""

from __future__ import annotations

from typing import Any

import orjson


def dumps(obj: Any, *, indent: int | None = None, default: Any = None) -> str:
    """Serialize to a JSON string. ``indent`` any truthy value → 2-space indent."""
    option = orjson.OPT_INDENT_2 if indent else None
    return orjson.dumps(obj, option=option, default=default).decode()


def dumpb(obj: Any, *, indent: int | None = None, default: Any = None) -> bytes:
    """Serialize to JSON bytes — use with ``Path.write_bytes()``."""
    option = orjson.OPT_INDENT_2 if indent else None
    return orjson.dumps(obj, option=option, default=default)


def loads(s: str | bytes) -> Any:
    """Deserialize a JSON string or bytes."""
    return orjson.loads(s)
