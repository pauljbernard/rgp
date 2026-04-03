from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class RgpModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ErrorDetail(RgpModel):
    field: str | None = None
    message: str


class ErrorBody(RgpModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    correlation_id: str
    retryable: bool = False


class ErrorEnvelope(RgpModel):
    error: ErrorBody


class PaginatedResponse(RgpModel, Generic[T]):
    items: list[T]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_count: int = Field(ge=0)
    total_pages: int = Field(ge=0)

    @classmethod
    def create(cls, items: list[T], page: int, page_size: int, total_count: int) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=ceil(total_count / page_size) if total_count else 0,
        )
