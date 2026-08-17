from fastapi import APIRouter

router = APIRouter()

@router.get("")
def get_chats() -> dict:
    return {"message": "Get chats"}
