"""API helper components — schemas, errors, and pagination.

These are building blocks for applications that expose an HTTP layer
on top of dataenginex (e.g. a FastAPI server).  They have no dependency
on any web framework and can be imported without extras.

Public API::

    from dataenginex.api import (
        BadRequestError, NotFoundError, ServiceUnavailableError,
        PaginatedResponse, paginate,
    )
    from dataenginex.api.schemas import PipelineResultResponse, PredictionRequest, ...
"""

from __future__ import annotations

from dataenginex.api.errors import (
    BadRequestError,
    DexAPIError,
    NotFoundError,
    ServiceUnavailableError,
)
from dataenginex.api.pagination import PaginatedResponse, PaginationMeta, paginate

__all__ = [
    # Errors
    "DexAPIError",
    "BadRequestError",
    "NotFoundError",
    "ServiceUnavailableError",
    # Pagination
    "PaginatedResponse",
    "PaginationMeta",
    "paginate",
]
