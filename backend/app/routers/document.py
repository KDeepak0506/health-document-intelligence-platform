from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentProcessingStatus,
    DocumentResponse,
)
from app.schemas.ocr import DocumentTextResponse
from app.services.document_service import (
    get_all_documents,
    get_document_by_id,
    get_document_text,
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
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    patient_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return upload_document(
        db=db,
        file=file,
        patient_id=patient_id,
        uploaded_by=current_user.user_id,
        background_tasks=background_tasks,
    )

@router.get(
    "",
    response_model=list[DocumentResponse],
)
def get_all_documents_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_all_documents(db=db)

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document_by_id_endpoint(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_document_status(
        db=db,
        document_id=document_id,
        status=status,
    )


@router.get(
    "/{document_id}/text",
    response_model=DocumentTextResponse,
)
def get_document_ocr_text(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the stored OCR text for a document owned by the authenticated user."""
    document = get_document_by_id(db=db, document_id=document_id)

    if document.uploaded_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return get_document_text(db=db, document_id=document_id)