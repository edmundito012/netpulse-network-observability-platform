from pydantic import BaseModel


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
