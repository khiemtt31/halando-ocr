from __future__ import annotations

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_owner_sub", "owner_sub"),
        Index("idx_documents_status", "status"),
        Index("idx_documents_created_at", "created_at"),
        Index("idx_documents_sha256", "sha256"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_sub: Mapped[str] = mapped_column(String(100), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False, default="default")
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    language_hint: Mapped[str | None] = mapped_column(String(32), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_original_key: Mapped[str] = mapped_column(Text, nullable=False)
    storage_ocr_pdf_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
