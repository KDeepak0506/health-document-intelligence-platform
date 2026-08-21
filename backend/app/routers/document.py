from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import (
    DocumentProcessingStatus,
    DocumentResponse,
)
from app.services.document_service import (
    get_all_documents,
    get_document_by_id,
    update_document_status,
    upload_document,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=201,
)
def upload_document_endpoint(
    file: UploadFile = File(...),
    patient_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    uploaded_by = UUID(
        "00000000-0000-0000-0000-000000000000"
    )  # Temporary Placeholder

    return upload_document(
        db=db,
        file=file,
        patient_id=patient_id,
        uploaded_by=uploaded_by,
    )

@router.get(
    "",
    response_model=list[DocumentResponse],
)
def get_all_documents_endpoint(
    db: Session = Depends(get_db),
):
    return get_all_documents(db=db)

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document_by_id_endpoint(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    return get_document_by_id(
        db=db,
        document_id=document_id,
    )

@router.patch(
    "/{document_id}/status",
    response_model=DocumentResponse,
)
def update_document_processing_status(
    document_id: UUID,
    status: DocumentProcessingStatus,
    db: Session = Depends(get_db),
):
    return update_document_status(
        db=db,
        document_id=document_id,
        status=status,
    )