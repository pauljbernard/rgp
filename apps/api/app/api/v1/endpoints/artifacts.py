from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_principal
from app.models.common import PaginatedResponse
from app.models.governance import ArtifactDetail, ArtifactRecord
from app.models.security import Principal
from app.services.governance_service import governance_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ArtifactRecord])
def list_artifacts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> PaginatedResponse[ArtifactRecord]:
    return governance_service.list_artifacts(page, page_size, principal.tenant_id)


@router.get("/{artifact_id}", response_model=ArtifactDetail)
def get_artifact(artifact_id: str, principal: Annotated[Principal, Depends(get_principal)]) -> ArtifactDetail:
    try:
        return governance_service.get_artifact(artifact_id, principal)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Artifact not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
