from __future__ import annotations

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.db.base import Base


class AppUser(Base):
    __tablename__ = "app_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    local_sub: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
