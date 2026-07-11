from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.search import DocumentSearch


def _snippet(text: str, query: str, window: int = 60) -> str:
    lowered = text.lower()
    needle = query.lower()
    index = lowered.find(needle)
    if index < 0:
        return text[: window * 2].strip()
    start = max(0, index - window)
    end = min(len(text), index + len(query) + window)
    snippet = text[start:end].strip()
    return snippet


async def search_documents(
    session: AsyncSession,
    *,
    query: str,
    owner_sub: str | None = None,
    admin: bool = False,
    document_id: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict[str, object]], int]:
    pattern = f"%{query.lower()}%"
    stmt = (
        select(DocumentSearch, Document)
        .join(Document, Document.id == DocumentSearch.document_id)
        .where(Document.status == "processed")
        .where(func.lower(DocumentSearch.search_vector).like(pattern))
        .order_by(DocumentSearch.document_id.asc(), DocumentSearch.page_number.asc())
    )
    count_stmt = (
        select(func.count())
        .select_from(DocumentSearch)
        .join(Document, Document.id == DocumentSearch.document_id)
        .where(Document.status == "processed")
        .where(func.lower(DocumentSearch.search_vector).like(pattern))
    )
    if owner_sub and not admin:
        stmt = stmt.where(DocumentSearch.owner_sub == owner_sub)
        count_stmt = count_stmt.where(DocumentSearch.owner_sub == owner_sub)
    if document_id:
        stmt = stmt.where(DocumentSearch.document_id == document_id)
        count_stmt = count_stmt.where(DocumentSearch.document_id == document_id)

    rows = (await session.execute(stmt.offset(offset).limit(limit))).all()
    total = int((await session.execute(count_stmt)).scalar_one())

    results: list[dict[str, object]] = []
    for search_row, document in rows:
        results.append(
            {
                "document_id": document.id,
                "document_filename": document.original_filename,
                "page_number": search_row.page_number,
                "snippet": _snippet(search_row.content, query),
                "matched_text": query,
                "status": document.status,
            }
        )
    return results, total
