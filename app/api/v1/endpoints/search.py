from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_session, require_roles
from app.core.errors import APIError
from app.core.security import Principal
from app.repositories.documents import get_document
from app.schemas.search import SearchHit, SearchResponse
from app.services.search import search_documents

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search_my_documents(
    q: str = Query(..., min_length=1),
    session=Depends(get_session),
    principal: Principal = Depends(require_roles("documents:read")),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> SearchResponse:
    items, total = await search_documents(
        session,
        query=q,
        owner_sub=principal.sub,
        admin=principal.is_admin,
        limit=limit,
        offset=offset,
    )
    return SearchResponse(limit=limit, offset=offset, total=total, items=[SearchHit(**item) for item in items])


@router.get("/documents/{document_id}/search", response_model=SearchResponse)
async def search_inside_document(
    document_id: str,
    q: str = Query(..., min_length=1),
    session=Depends(get_session),
    principal: Principal = Depends(require_roles("documents:read")),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> SearchResponse:
    document = await get_document(session, document_id, owner_sub=principal.sub, admin=principal.is_admin)
    if document is None:
        raise APIError("DOCUMENT_NOT_FOUND", "Document not found or access denied.", 404)
    items, total = await search_documents(
        session,
        query=q,
        owner_sub=principal.sub,
        admin=principal.is_admin,
        document_id=document_id,
        limit=limit,
        offset=offset,
    )
    return SearchResponse(limit=limit, offset=offset, total=total, items=[SearchHit(**item) for item in items])
