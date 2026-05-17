from typing import Generic, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel


T = TypeVar("T")


class PaginatedResponse(GenericModel, Generic[T]):
    items: list[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int