from typing import List, Dict, Any
from fastapi import APIRouter

router = APIRouter()

AVAILABLE_LANGUAGES: List[Dict[str, Any]] = [
    {"code": "en", "name": "English", "native_name": "English", "enabled": True},
    {"code": "ta", "name": "Tamil", "native_name": "தமிழ்", "enabled": True},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी", "enabled": True},
    {"code": "te", "name": "Telugu", "native_name": "తెలుగు", "enabled": True},
    {"code": "kn", "name": "Kannada", "native_name": "கன்னட / ಕನ್ನಡ", "enabled": True},
    {"code": "ml", "name": "Malayalam", "native_name": "മലയാളം", "enabled": True},
    {"code": "bn", "name": "Bengali", "native_name": "বাংলা", "enabled": True},
    {"code": "mr", "name": "Marathi", "native_name": "मराठी", "enabled": True},
    {"code": "gu", "name": "Gujarati", "native_name": "ગુજરાતી", "enabled": True},
    {"code": "pa", "name": "Punjabi", "native_name": "ਪੰਜਾਬੀ", "enabled": False},
    {"code": "or", "name": "Odia", "native_name": "ଓଡ଼ିଆ", "enabled": False},
    {"code": "as", "name": "Assamese", "native_name": "অসমীয়া", "enabled": False},
    {"code": "ur", "name": "Urdu", "native_name": "اردو", "enabled": False},
]


@router.get("", response_model=List[Dict[str, Any]])
def get_languages() -> List[Dict[str, Any]]:
    return AVAILABLE_LANGUAGES
