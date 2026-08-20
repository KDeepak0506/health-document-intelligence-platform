from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.document import Document

from datetime import datetime, timezone
from app.schemas.document import DocumentProcessingStatus


UPLOAD_DIR = Path("uploads/documents")

ALLOWED_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}


def upload_document(
    db: Session,
    file: UploadFile,
    patient_id: UUID | None,
    uploaded_by: UUID,
) -> Document:

    # 1. Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type",
        )

    # 2. Make sure upload directory exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # 3. Create database record
    document = Document(
        patient_id=patient_id,
        uploaded_by=uploaded_by,
        file_name=file.filename,
        file_type=file.content_type,
        file_url="",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # 4. Create file path using document ID
    file_extension = Path(file.filename).suffix
    file_path = UPLOAD_DIR / f"{document.document_id}{file_extension}"

    # 5. Save uploaded file
    try:
        with file_path.open("wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                buffer.write(chunk)

    except Exception:
        db.delete(document)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail="Failed to save uploaded file",
        )

    # 6. Store file path in database
    document.file_url = str(file_path)

    db.commit()
    db.refresh(document)

    return document

def update_document_status(
    db: Session,
    document_id: UUID,
    status: DocumentProcessingStatus,
) -> Document:

    document = (
        db.query(Document)
        .filter(Document.document_id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    document.processing_status = status.value

    if status == DocumentProcessingStatus.COMPLETED:
        document.processed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(document)

    return document

def get_all_documents(
    db: Session,
) -> list[Document]:

    documents = (
        db.query(Document)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    return documents

def get_document_by_id(
    db: Session,
    document_id: UUID,
) -> Document:

    document = (
        db.query(Document)
        .filter(Document.document_id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document