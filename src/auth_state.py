SESSION = {"token": None, "user": None}


def is_logged_in() -> bool:
    return SESSION["token"] is not None


def set_session(token: str, user: dict) -> None:
    SESSION["token"] = token
    SESSION["user"] = user


def clear_session() -> None:
    SESSION["token"] = None
    SESSION["user"] = None
