from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def get_admin_status() -> dict:
    return {"message": "Admin active"}
