"""
Cursor-based pagination utilities for the DEX API.

Usage::

    from dataenginex.api.pagination import PaginatedResponse, paginate

    @app.get("/api/v1/items")
    def list_items(cursor: str | None = None, limit: int = 20):
        all_items = get_all_items()
        return paginate(all_items, cursor=cursor, limit=limit)
"""

from __future__ import annotations

import base64
from typing import Any, TypeVar

from pydantic import BaseModel, Field

from dataenginex import _json

T = TypeVar("T")

__all__ = [
    "PaginatedResponse",
    "PaginationMeta",
    "decode_cursor",
    "encode_cursor",
    "paginate",
]


class PaginationMeta(BaseModel):
    """Pagination metadata returned alongside results."""

    total: int = Field(description="Total number of items")
    limit: int = Field(description="Page size")
    has_next: bool = Field(description="Whether more items exist")
    next_cursor: str | None = Field(None, description="Opaque cursor for next page")
    has_previous: bool = Field(default=False, description="Whether previous items exist")


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    data: list[Any] = Field(default_factory=list)
    pagination: PaginationMeta


def encode_cursor(offset: int) -> str:
    """Encode an integer offset into an opaque base64 cursor."""
    return base64.urlsafe_b64encode(_json.dumps({"o": offset}).encode()).decode()


def decode_cursor(cursor: str) -> int:
    """Decode a cursor back to an integer offset.

    Raises:
        ValueError: If the cursor is malformed or cannot be decoded.
    """
    try:
        data = _json.loads(base64.urlsafe_b64decode(cursor))
        return int(data["o"])
    except (ValueError, KeyError, UnicodeDecodeError) as exc:
        msg = f"Invalid pagination cursor: {cursor!r}"
        raise ValueError(msg) from exc


def paginate(
    items: list[Any],
    *,
    cursor: str | None = None,
    limit: int = 20,
    max_limit: int = 100,
) -> PaginatedResponse:
    """Slice *items* and return a ``PaginatedResponse``.

    Parameters
    ----------
    items:
        Full list of items to paginate.
    cursor:
        Opaque cursor from a previous response (or *None* for the first page).
    limit:
        Number of items per page.
    max_limit:
        Hard ceiling on *limit* to prevent abuse.
    """
    limit = min(max(1, limit), max_limit)

    if cursor:
        try:
            offset = decode_cursor(cursor)
        except ValueError:
            offset = 0  # Reset to first page on invalid cursor
    else:
        offset = 0
    total = len(items)

    page = items[offset : offset + limit]
    has_next = (offset + limit) < total
    next_cursor = encode_cursor(offset + limit) if has_next else None
    has_previous = offset > 0

    return PaginatedResponse(
        data=page,
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            has_next=has_next,
            next_cursor=next_cursor,
            has_previous=has_previous,
        ),
    )
