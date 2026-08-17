from fastapi import APIRouter

router = APIRouter()

@router.get("")
def get_quizzes() -> dict:
    return {"message": "Get quizzes"}
