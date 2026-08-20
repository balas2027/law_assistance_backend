from typing import Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# In-memory session preference store
_user_preferences: Dict[str, Any] = {
    "preferred_language": None
}


class PreferenceUpdate(BaseModel):
    preferred_language: Optional[str] = None


@router.get("/preferences")
def get_user_preferences() -> dict:
    return {"preferred_language": _user_preferences.get("preferred_language")}


@router.patch("/preferences")
def update_user_preferences(payload: PreferenceUpdate) -> dict:
    _user_preferences["preferred_language"] = payload.preferred_language
    return {"preferred_language": _user_preferences.get("preferred_language")}
