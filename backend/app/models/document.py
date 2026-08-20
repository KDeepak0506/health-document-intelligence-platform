from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Numeric , func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    patient_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
    )

    uploaded_by: Mapped[UUID] = mapped_column(
        nullable=False,
    )

    file_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    file_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    file_url: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    document_type: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    processing_status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="Pending",
    )

    ocr_quality_score: Mapped[float | None] = mapped_column(
        Numeric,
        nullable=True,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )