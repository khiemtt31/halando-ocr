from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utcnow
from app.models.document_page import DocumentPage
from app.models.search import DocumentSearch


async def replace_document_pages(
    session: AsyncSession,
    *,
    document_id: str,
    owner_sub: str,
    pages: list[dict[str, object]],
) -> list[DocumentPage]:
    await session.execute(delete(DocumentPage).where(DocumentPage.document_id == document_id))
    await session.execute(delete(DocumentSearch).where(DocumentSearch.document_id == document_id))
    now = utcnow()
    inserted: list[DocumentPage] = []
    for page in pages:
        page_number = int(page["page_number"])
        text_content = str(page.get("text_content") or "")
        confidence = page.get("confidence")
        width = page.get("width")
        height = page.get("height")
        document_page = DocumentPage(
            id=str(uuid4()),
            document_id=document_id,
            page_number=page_number,
            text_content=text_content,
            confidence=confidence,
            width=int(width) if width is not None else None,
            height=int(height) if height is not None else None,
            created_at=now,
            updated_at=now,
        )
        document_search = DocumentSearch(
            id=str(uuid4()),
            document_id=document_id,
            owner_sub=owner_sub,
            page_number=page_number,
            content=text_content,
            search_vector=text_content.lower(),
            created_at=now,
            updated_at=now,
        )
        session.add(document_page)
        session.add(document_search)
        inserted.append(document_page)
    await session.flush()
    return inserted


async def get_document_pages(session: AsyncSession, document_id: str) -> list[DocumentPage]:
    stmt = select(DocumentPage).where(DocumentPage.document_id == document_id).order_by(DocumentPage.page_number.asc())
    return list((await session.scalars(stmt)).all())
