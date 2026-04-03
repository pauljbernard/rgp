from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import get_principal
from app.models.security import Principal
from app.models.template import TemplateRecord
from app.services.template_service import template_service


router = APIRouter()


@router.get("", response_model=list[TemplateRecord])
def list_templates(principal: Annotated[Principal, Depends(get_principal)]) -> list[TemplateRecord]:
    return template_service.list_templates(principal)
