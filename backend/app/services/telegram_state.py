from typing import Any

_states: dict[str, dict[str, Any]] = {}


def get_state(chat_id: str) -> str | None:
    return _states.get(chat_id, {}).get("state")


def set_state(chat_id: str, state: str) -> None:
    _states.setdefault(chat_id, {})["state"] = state


def update_data(chat_id: str, **kwargs: Any) -> None:
    _states.setdefault(chat_id, {}).update(kwargs)


def get_data(chat_id: str) -> dict[str, Any]:
    return {k: v for k, v in _states.get(chat_id, {}).items() if k != "state"}


def clear_state(chat_id: str) -> None:
    _states.pop(chat_id, None)
