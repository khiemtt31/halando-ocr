from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utcnow
from app.models.document import Document


async def create_document(session: AsyncSession, **values: object) -> Document:
    raw_id = values.pop("id", None)
    document_id = str(raw_id if raw_id is not None else uuid4())
    document = Document(id=document_id, **values)
    session.add(document)
    await session.flush()
    return document


async def get_document(
    session: AsyncSession,
    document_id: str,
    *,
    owner_sub: str | None = None,
    admin: bool = False,
    include_deleted: bool = False,
) -> Document | None:
    stmt = select(Document).where(Document.id == document_id)
    if owner_sub and not admin:
        stmt = stmt.where(Document.owner_sub == owner_sub)
    if not include_deleted:
        stmt = stmt.where(Document.status != "deleted")
    return (await session.scalars(stmt)).first()


def _apply_visibility(stmt: Select, *, owner_sub: str | None = None, admin: bool = False, include_deleted: bool = False) -> Select:
    if owner_sub and not admin:
        stmt = stmt.where(Document.owner_sub == owner_sub)
    if not include_deleted:
        stmt = stmt.where(Document.status != "deleted")
    return stmt


async def list_documents(
    session: AsyncSession,
    *,
    owner_sub: str | None = None,
    admin: bool = False,
    include_deleted: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Document], int]:
    stmt = _apply_visibility(select(Document), owner_sub=owner_sub, admin=admin, include_deleted=include_deleted)
    stmt = stmt.order_by(Document.created_at.desc()).offset(offset).limit(limit)
    items = list((await session.scalars(stmt)).all())

    count_stmt = _apply_visibility(select(func.count()).select_from(Document), owner_sub=owner_sub, admin=admin, include_deleted=include_deleted)
    total = int((await session.execute(count_stmt)).scalar_one())
    return items, total


async def update_document_status(session: AsyncSession, document: Document, status: str) -> Document:
    document.status = status
    document.updated_at = utcnow()
    await session.flush()
    return document


async def mark_document_deleted(session: AsyncSession, document: Document) -> Document:
    document.status = "deleted"
    document.updated_at = utcnow()
    await session.flush()
    return document
