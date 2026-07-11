from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.search import search_documents as repo_search_documents


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
    return await repo_search_documents(
        session,
        query=query,
        owner_sub=owner_sub,
        admin=admin,
        document_id=document_id,
        limit=limit,
        offset=offset,
    )
