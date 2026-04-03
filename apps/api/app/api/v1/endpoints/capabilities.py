from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_principal
from app.models.common import PaginatedResponse
from app.models.governance import CapabilityDetail, CapabilityRecord
from app.models.security import Principal
from app.services.governance_service import governance_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[CapabilityRecord])
def list_capabilities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> PaginatedResponse[CapabilityRecord]:
    return governance_service.list_capabilities(page, page_size, principal)


@router.get("/{capability_id}", response_model=CapabilityDetail)
def get_capability(capability_id: str, principal: Annotated[Principal, Depends(get_principal)]) -> CapabilityDetail:
    try:
        return governance_service.get_capability(capability_id, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capability not found") from None
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Capability not accessible for tenant") from None
