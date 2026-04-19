from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl, Field


class ExtractRequest(BaseModel):
    url: HttpUrl


class ExtractResponse(BaseModel):
    url: HttpUrl
    final_url: HttpUrl
    title: str
    source: str | None = None
    extracted_text: str
    important_passages: list[str] = Field(default_factory=list)
    content_length: int


class ExtractHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    final_url: str | None = None
    title: str
    source: str | None = None
    content_length: int
    created_at: datetime