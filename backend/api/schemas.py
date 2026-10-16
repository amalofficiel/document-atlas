from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(3, ge=1, le=10)


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
