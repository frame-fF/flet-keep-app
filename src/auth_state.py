SESSION = {"token": None, "refresh": None, "user": None}


def is_logged_in() -> bool:
    return SESSION["token"] is not None


def get_token() -> str | None:
    return SESSION["token"]


def get_refresh_token() -> str | None:
    return SESSION["refresh"]


def set_session(token: str, refresh: str, user: dict) -> None:
    SESSION["token"] = token
    SESSION["refresh"] = refresh
    SESSION["user"] = user


def clear_session() -> None:
    SESSION["token"] = None
    SESSION["refresh"] = None
    SESSION["user"] = None
