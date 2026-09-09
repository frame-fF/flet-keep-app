import httpx

BASE_URL = "http://127.0.0.1:8000"


class ApiError(Exception):
    pass


async def _post(path: str, json: dict) -> dict:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        r = await client.post(path, json=json)
    if r.status_code >= 400:
        raise ApiError(r.text)
    return r.json()


async def register(username: str, email: str, password: str) -> dict:
    return await _post(
        "/api/user/register/",
        {"username": username, "email": email, "password": password},
    )


async def login(username_or_email: str, password: str) -> dict:
    return await _post(
        "/api/user/login/",
        {"username": username_or_email, "password": password},
    )
