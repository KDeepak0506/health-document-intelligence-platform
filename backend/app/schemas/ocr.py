from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentTextResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    raw_text: str
    page_count: int | None = None
    confidence: float | None = None
    layout: dict | None = None
    ocr_engine: str
    processing_time_ms: int | None = None
    created_at: datetime
