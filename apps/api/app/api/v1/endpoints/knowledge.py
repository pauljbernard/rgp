from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_principal
from app.models.common import PaginatedResponse
from app.models.knowledge import CreateKnowledgeArtifactRequest, KnowledgeArtifactRecord, KnowledgeVersionRecord
from app.models.security import Principal
from app.services.knowledge_service import knowledge_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[KnowledgeArtifactRecord])
def list_knowledge_artifacts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    query: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> PaginatedResponse[KnowledgeArtifactRecord]:
    return knowledge_service.list_artifacts(principal.tenant_id, page, page_size, query, status_filter)


@router.post("", response_model=KnowledgeArtifactRecord, status_code=status.HTTP_201_CREATED)
def create_knowledge_artifact(
    payload: CreateKnowledgeArtifactRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> KnowledgeArtifactRecord:
    return knowledge_service.create_artifact(payload, principal.user_id, principal.tenant_id)


@router.get("/{artifact_id}", response_model=KnowledgeArtifactRecord)
def get_knowledge_artifact(
    artifact_id: str,
    principal: Annotated[Principal, Depends(get_principal)],
) -> KnowledgeArtifactRecord:
    try:
        return knowledge_service.get_artifact(artifact_id, principal.tenant_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Knowledge artifact not found") from None


@router.get("/{artifact_id}/versions", response_model=list[KnowledgeVersionRecord])
def list_knowledge_versions(
    artifact_id: str,
    principal: Annotated[Principal, Depends(get_principal)],
) -> list[KnowledgeVersionRecord]:
    try:
        return knowledge_service.list_versions(artifact_id, principal.tenant_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Knowledge artifact not found") from None


@router.post("/{artifact_id}/publish", response_model=KnowledgeArtifactRecord)
def publish_knowledge_artifact(
    artifact_id: str,
    principal: Annotated[Principal, Depends(get_principal)],
) -> KnowledgeArtifactRecord:
    try:
        return knowledge_service.publish_artifact(artifact_id, principal.user_id, principal.tenant_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Knowledge artifact not found") from None


@router.get("/context/request/{request_id}", response_model=list[KnowledgeArtifactRecord])
def get_request_knowledge_context(
    request_id: str,
    max_items: int = Query(default=5, ge=1, le=20),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[KnowledgeArtifactRecord]:
    return knowledge_service.retrieve_for_context(request_id, principal.tenant_id, max_items=max_items)
