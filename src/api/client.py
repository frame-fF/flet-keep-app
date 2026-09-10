import httpx

from models import ChecklistItem, LoginResponse, Note

BASE_URL = "http://127.0.0.1:8000"


class ApiError(Exception):
    def __init__(self, message: str, errors: dict | None = None):
        super().__init__(message)
        self.errors = errors or {}


def _raise_for_error(r: httpx.Response) -> None:
    try:
        errors = r.json()
    except ValueError:
        errors = {}
    raise ApiError(r.text, errors=errors if isinstance(errors, dict) else {})


async def _post(path: str, json: dict, token: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        r = await client.post(path, json=json, headers=headers)
    if r.status_code >= 400:
        _raise_for_error(r)
    return r.json()


async def _get(path: str, token: str | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        r = await client.get(path, headers=headers)
    if r.status_code >= 400:
        _raise_for_error(r)
    return r.json()


async def _patch(path: str, json: dict, token: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        r = await client.patch(path, json=json, headers=headers)
    if r.status_code >= 400:
        _raise_for_error(r)
    return r.json()


def split_errors(errors: dict) -> tuple[str, dict[str, str]]:
    """Split a DRF-style error dict into a general message and per-field messages."""
    general = errors.get("detail") or errors.get("non_field_errors")
    if isinstance(general, list):
        general = general[0] if general else None

    fields = {
        key: (value[0] if isinstance(value, list) else str(value))
        for key, value in errors.items()
        if key not in ("detail", "non_field_errors")
    }
    return (str(general) if general else "", fields)


async def register(username: str, email: str, password: str, password2: str) -> dict:
    return await _post(
        "/api/user/register/",
        {"username": username, "email": email, "password": password, "password2": password2},
    )


async def login(username_or_email: str, password: str) -> LoginResponse:
    data = await _post(
        "/api/user/login/",
        {"username": username_or_email, "password": password},
    )
    return LoginResponse(**data)


async def refresh_token(refresh: str) -> dict:
    return await _post("/api/user/token/refresh/", {"refresh": refresh})


async def create_note(
    token: str,
    title: str,
    content: str,
    color: str = "default",
    is_pinned: bool = False,
    labels: list[str] | None = None,
    checklist_items: list[ChecklistItem] | None = None,
) -> Note:
    data = await _post(
        "/api/keep/notes/",
        {
            "title": title,
            "content": content,
            "color": color,
            "is_pinned": is_pinned,
            "labels": labels or [],
            "checklist_items": [item.model_dump(exclude_none=True) for item in (checklist_items or [])],
        },
        token=token,
    )
    return Note(**data)


async def list_notes(token: str) -> list[Note]:
    data = await _get("/api/keep/notes/", token=token)
    return [Note(**item) for item in data]


async def update_note(
    token: str,
    note_id: int,
    title: str | None = None,
    content: str | None = None,
    color: str | None = None,
    is_pinned: bool | None = None,
    labels: list[str] | None = None,
    checklist_items: list[ChecklistItem] | None = None,
) -> Note:
    payload = {}
    if title is not None:
        payload["title"] = title
    if content is not None:
        payload["content"] = content
    if color is not None:
        payload["color"] = color
    if is_pinned is not None:
        payload["is_pinned"] = is_pinned
    if labels is not None:
        payload["labels"] = labels
    if checklist_items is not None:
        payload["checklist_items"] = [item.model_dump(exclude_none=True) for item in checklist_items]

    data = await _patch(f"/api/keep/notes/{note_id}/", payload, token=token)
    return Note(**data)


async def logout(token: str, refresh: str) -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        r = await client.post(
            "/api/user/logout/",
            headers={"Authorization": f"Bearer {token}"},
            json={"refresh": refresh},
        )
    if r.status_code >= 400:
        _raise_for_error(r)
