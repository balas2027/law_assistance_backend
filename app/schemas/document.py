from typing import Optional
from pydantic import BaseModel, ConfigDict

class DocumentBase(BaseModel):
    filename: str

class DocumentCreate(DocumentBase):
    content: str

class Document(DocumentBase):
    id: int
    vector_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
