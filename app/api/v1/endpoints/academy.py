from fastapi import APIRouter

router = APIRouter()

@router.get("")
def get_academy_courses() -> dict:
    return {"message": "Get academy courses"}
