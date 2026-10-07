"""Response envelopes, list/pagination parameters and shared field types."""

import math
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    StringConstraints,
)

DEFAULT_SUCCESS_MESSAGE = "Thành công"

# Decimal columns are returned as JSON numbers (Pydantic would otherwise emit strings).
DecimalNumber = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


def _blank_to_none(value: object) -> object:
    return None if isinstance(value, str) and not value.strip() else value


# Input field types shared by create/update schemas.
Code = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_upper=True,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.\-]*$",
    ),
]
ShortName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
LongName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
OptionalText = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True)] | None,
    BeforeValidator(_blank_to_none),
]
OptionalAddress = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None,
    BeforeValidator(_blank_to_none),
]


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class ListParams(BaseModel):
    """Query parameters shared by every list endpoint; subclasses add filters and `sort_by`."""

    page: int = Field(1, ge=1, description="Trang hiện tại (bắt đầu từ 1)")
    page_size: int = Field(20, ge=1, le=100, description="Số bản ghi mỗi trang")
    sort_by: str
    sort_order: SortOrder = SortOrder.ASC


class SearchableListParams(ListParams):
    search: str | None = Field(None, max_length=100, description="Từ khóa tìm kiếm")


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return math.ceil(self.total / self.page_size) if self.total else 0


class ApiResponse[T](BaseModel):
    success: bool = True
    message: str = DEFAULT_SUCCESS_MESSAGE
    data: T


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse[T](BaseModel):
    success: bool = True
    message: str = DEFAULT_SUCCESS_MESSAGE
    data: list[T]
    pagination: PaginationMeta


def paginated[S: BaseModel](page: Page[Any], schema: type[S]) -> PaginatedResponse[S]:
    """Serialize a repository page of ORM entities into the list envelope."""
    return PaginatedResponse(
        data=[schema.model_validate(item) for item in page.items],
        pagination=PaginationMeta(
            page=page.page,
            page_size=page.page_size,
            total=page.total,
            total_pages=page.total_pages,
        ),
    )


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorInfo(BaseModel):
    code: str
    details: list[ErrorDetail] | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: ErrorInfo
