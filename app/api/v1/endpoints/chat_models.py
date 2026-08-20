from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    query: str
    source_type: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        return value.strip()



class SourceDocument(BaseModel):
    content: str
    metadata: Dict[str, Any]
    distance: Optional[float] = None


class ChatResponse(BaseModel):
    answer: str
    source_type: Optional[str] = None
    sources: List[SourceDocument]


class SuggestedPrompt(BaseModel):
    id: str
    icon: str
    text: str


class ChatConfigResponse(BaseModel):
    heading: str
    description: str
    suggested_prompts: List[SuggestedPrompt]
