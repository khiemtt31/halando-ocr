from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.db.base import Base


class DocumentSearch(Base):
    __tablename__ = "document_search"
    __table_args__ = (
        Index("idx_document_search_document_id", "document_id"),
        Index("idx_document_search_owner_sub", "owner_sub"),
        Index("idx_document_search_page_number", "page_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    owner_sub: Mapped[str] = mapped_column(String(100), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    search_vector: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
