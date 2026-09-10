from pydantic import BaseModel

NOTE_COLORS = [
    "default",
    "red",
    "orange",
    "yellow",
    "green",
    "teal",
    "blue",
    "purple",
    "pink",
    "brown",
    "gray",
]


class ChecklistItem(BaseModel):
    id: int | None = None
    text: str
    is_checked: bool = False
    order: int


class Note(BaseModel):
    id: int
    title: str
    content: str = ""
    color: str = "default"
    labels: list[str] = []
    checklist_items: list[ChecklistItem] = []
    is_pinned: bool = False
    is_archived: bool = False
    is_trashed: bool = False
    created_at: str | None = None
    updated_at: str | None = None
