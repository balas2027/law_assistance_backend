from typing import Optional
from pydantic import BaseModel, ConfigDict

class AdminLogBase(BaseModel):
    action: str
    details: Optional[str] = None

class AdminLogCreate(AdminLogBase):
    pass

class AdminLog(AdminLogBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
