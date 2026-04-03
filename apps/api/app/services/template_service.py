from app.models.security import Principal
from app.models.template import (
    CreateTemplateVersionRequest,
    TemplateRecord,
    TemplateStatus,
    TemplateStatusActionRequest,
    TemplateValidationResult,
    UpdateTemplateDefinitionRequest,
)
from app.repositories.governance_repository import governance_repository


class TemplateService:
    def list_templates(self, principal: Principal) -> list[TemplateRecord]:
        return governance_repository.list_templates(principal.tenant_id, include_non_published=False)

    def list_admin_templates(self, principal: Principal) -> list[TemplateRecord]:
        return governance_repository.list_templates(principal.tenant_id, include_non_published=True)

    def create_template_version(self, payload: CreateTemplateVersionRequest, principal: Principal) -> TemplateRecord:
        return governance_repository.create_template_version(payload, principal.user_id, principal.tenant_id)

    def update_template_definition(self, template_id: str, version: str, payload: UpdateTemplateDefinitionRequest, principal: Principal) -> TemplateRecord:
        return governance_repository.update_template_definition(template_id, version, payload, principal.user_id, principal.tenant_id)

    def validate_template_definition(self, template_id: str, version: str, principal: Principal) -> TemplateValidationResult:
        return governance_repository.validate_template_definition(template_id, version, principal.tenant_id)

    def delete_template_version(self, template_id: str, version: str, principal: Principal) -> None:
        return governance_repository.delete_template_version(template_id, version, principal.user_id, principal.tenant_id)

    def publish_template_version(self, template_id: str, version: str, payload: TemplateStatusActionRequest, principal: Principal) -> TemplateRecord:
        return governance_repository.update_template_status(template_id, version, TemplateStatus.PUBLISHED, principal.user_id, principal.tenant_id, payload.note)

    def deprecate_template_version(self, template_id: str, version: str, payload: TemplateStatusActionRequest, principal: Principal) -> TemplateRecord:
        return governance_repository.update_template_status(template_id, version, TemplateStatus.DEPRECATED, principal.user_id, principal.tenant_id, payload.note)


template_service = TemplateService()
