from uuid import UUID
from pydantic import BaseModel
from enum import Enum


class DocumentProcessingStatus(str, Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"


class DocumentResponse(BaseModel):
    document_id: UUID
    patient_id: UUID | None
    uploaded_by: UUID
    file_name: str
    file_type: str
    file_url: str
    document_type: str | None
    processing_status: DocumentProcessingStatus