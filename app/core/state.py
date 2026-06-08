from dataclasses import dataclass

@dataclass
class AppState:
    user_id: str
    school_id: str
    role: str
    name: str
    token: str | None = None

# Almacén simple en memoria
_state = {}

def set_app_state(page, user_data: dict):
    _state["current"] = AppState(
        user_id=user_data["_id"],
        school_id=user_data["schoolId"],
        role=user_data["role"],
        name=user_data["name"],
        token=user_data.get("token"),
    )

def get_app_state(page):
    return _state.get("current", None)