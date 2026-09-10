import httpx

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


async def login(username_or_email: str, password: str) -> dict:
    return await _post(
        "/api/user/login/",
        {"username": username_or_email, "password": password},
    )


async def refresh_token(refresh: str) -> dict:
    return await _post("/api/user/token/refresh/", {"refresh": refresh})


async def create_note(
    token: str,
    title: str,
    content: str,
    color: str = "default",
    is_pinned: bool = False,
    labels: list[str] | None = None,
    checklist_items: list[dict] | None = None,
) -> dict:
    return await _post(
        "/api/keep/notes/",
        {
            "title": title,
            "content": content,
            "color": color,
            "is_pinned": is_pinned,
            "labels": labels or [],
            "checklist_items": checklist_items or [],
        },
        token=token,
    )


async def list_notes(token: str) -> list[dict]:
    return await _get("/api/keep/notes/", token=token)


async def update_note(token: str, note_id: int, **fields) -> dict:
    return await _patch(f"/api/keep/notes/{note_id}/", fields, token=token)


async def logout(token: str, refresh: str) -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        r = await client.post(
            "/api/user/logout/",
            headers={"Authorization": f"Bearer {token}"},
            json={"refresh": refresh},
        )
    if r.status_code >= 400:
        _raise_for_error(r)
