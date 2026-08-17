from fastapi import APIRouter

router = APIRouter()

@router.get("")
def get_documents() -> dict:
    return {"message": "Get documents"}
