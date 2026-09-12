from pydantic import BaseModel

from app.schemas.pagination import PaginatedResponse


class ExampleItem(BaseModel):
    id: int
    name: str


def test_paginated_response_serializes_typed_items() -> None:
    response = PaginatedResponse[ExampleItem](
        items=[ExampleItem(id=1, name="router")],
        total_count=1,
        page=1,
        page_size=20,
        total_pages=1,
    )

    assert response.model_dump() == {
        "items": [{"id": 1, "name": "router"}],
        "total_count": 1,
        "page": 1,
        "page_size": 20,
        "total_pages": 1,
    }


def test_paginated_response_validates_item_type() -> None:
    response = PaginatedResponse[ExampleItem](
        items=[{"id": 2, "name": "switch"}],
        total_count=1,
        page=1,
        page_size=20,
        total_pages=1,
    )

    assert isinstance(response.items[0], ExampleItem)
    assert response.items[0].name == "switch"
