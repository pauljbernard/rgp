from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_principal
from app.models.domain_pack import CreateDomainPackRequest, DomainPackComparison, DomainPackDetail, DomainPackInstallation, DomainPackLineageEntry, DomainPackRecord
from app.models.security import Principal
from app.services.domain_pack_service import domain_pack_service


router = APIRouter()


@router.get("", response_model=list[DomainPackRecord])
def list_domain_packs(
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return domain_pack_service.list_packs(principal.tenant_id)


@router.post("", response_model=DomainPackRecord, status_code=status.HTTP_201_CREATED)
def create_domain_pack(
    payload: CreateDomainPackRequest,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return domain_pack_service.create_pack(payload, principal.tenant_id)


@router.get("/{pack_id}", response_model=DomainPackDetail)
def get_domain_pack(
    pack_id: str,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    try:
        return domain_pack_service.get_pack_detail(pack_id, principal.tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Domain pack not found") from exc


@router.post("/{pack_id}/activate", response_model=DomainPackRecord)
def activate_domain_pack(
    pack_id: str,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    try:
        return domain_pack_service.activate_pack(pack_id, principal.user_id, principal.tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Domain pack not found") from exc


@router.post("/{pack_id}/install", response_model=DomainPackInstallation, status_code=status.HTTP_201_CREATED)
def install_domain_pack(
    pack_id: str,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    try:
        return domain_pack_service.install_pack(pack_id, principal.user_id, principal.tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Domain pack not found") from exc


@router.get("/{pack_id}/validate", response_model=list[str])
def validate_domain_pack(
    pack_id: str,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    try:
        detail = domain_pack_service.get_pack_detail(pack_id, principal.tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Domain pack not found") from exc
    if detail.pack.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=404, detail="Domain pack not found")
    return domain_pack_service.validate_pack(pack_id)


@router.get("/{pack_id}/compare", response_model=DomainPackComparison)
def compare_domain_pack(
    pack_id: str,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    try:
        detail = domain_pack_service.get_pack_detail(pack_id, principal.tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Domain pack not found") from exc
    if detail.pack.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=404, detail="Domain pack not found")
    return domain_pack_service.compare_pack(pack_id, principal.tenant_id)


@router.get("/{pack_id}/lineage", response_model=list[DomainPackLineageEntry])
def list_domain_pack_lineage(
    pack_id: str,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    try:
        detail = domain_pack_service.get_pack_detail(pack_id, principal.tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Domain pack not found") from exc
    if detail.pack.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=404, detail="Domain pack not found")
    return domain_pack_service.list_pack_lineage(pack_id, principal.tenant_id)
