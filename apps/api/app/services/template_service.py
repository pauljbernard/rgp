from app.core.config import settings
from app.models.security import Principal
from app.models.template import (
    CreateTemplateVersionRequest,
    TemplateRecord,
    TemplateStatus,
    TemplateStatusActionRequest,
    TemplateValidationResult,
    UpdateTemplateDefinitionRequest,
)
from app.persistence import DynamoDbGovernancePersistenceAdapter, SqlAlchemyGovernancePersistenceAdapter, TemplatePersistencePort


class TemplateService:
    def __init__(self, template_store: TemplatePersistencePort) -> None:
        self._template_store = template_store

    def list_templates(self, principal: Principal) -> list[TemplateRecord]:
        return self._template_store.list_templates(principal.tenant_id, include_non_published=False)

    def list_admin_templates(self, principal: Principal) -> list[TemplateRecord]:
        return self._template_store.list_templates(principal.tenant_id, include_non_published=True)

    def create_template_version(self, payload: CreateTemplateVersionRequest, principal: Principal) -> TemplateRecord:
        return self._template_store.create_template_version(payload, principal.user_id, principal.tenant_id)

    def update_template_definition(self, template_id: str, version: str, payload: UpdateTemplateDefinitionRequest, principal: Principal) -> TemplateRecord:
        return self._template_store.update_template_definition(template_id, version, payload, principal.user_id, principal.tenant_id)

    def validate_template_definition(self, template_id: str, version: str, principal: Principal) -> TemplateValidationResult:
        return self._template_store.validate_template_definition(template_id, version, principal.tenant_id)

    def delete_template_version(self, template_id: str, version: str, principal: Principal) -> None:
        return self._template_store.delete_template_version(template_id, version, principal.user_id, principal.tenant_id)

    def publish_template_version(self, template_id: str, version: str, payload: TemplateStatusActionRequest, principal: Principal) -> TemplateRecord:
        return self._template_store.update_template_status(template_id, version, TemplateStatus.PUBLISHED, principal.user_id, principal.tenant_id, payload.note)

    def deprecate_template_version(self, template_id: str, version: str, payload: TemplateStatusActionRequest, principal: Principal) -> TemplateRecord:
        return self._template_store.update_template_status(template_id, version, TemplateStatus.DEPRECATED, principal.user_id, principal.tenant_id, payload.note)


def _build_template_store() -> TemplatePersistencePort:
    backend = (settings.template_persistence_backend or settings.persistence_backend or "sqlalchemy").lower()
    if backend == "dynamodb":
        return DynamoDbGovernancePersistenceAdapter()
    return SqlAlchemyGovernancePersistenceAdapter()


template_service = TemplateService(_build_template_store())
