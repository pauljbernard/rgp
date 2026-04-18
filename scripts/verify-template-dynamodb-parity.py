from __future__ import annotations

import json
from uuid import uuid4

from app.persistence.dynamodb_bootstrap import initialize_template_slice
from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter
from app.persistence.sql_governance_adapter import SqlAlchemyGovernancePersistenceAdapter
from app.models.template import CreateTemplateVersionRequest, TemplateStatus, UpdateTemplateDefinitionRequest


def _record_dict(record):
    return {
        "id": record.id,
        "version": record.version,
        "name": record.name,
        "description": record.description,
        "status": record.status.value if isinstance(record.status, TemplateStatus) else str(record.status),
        "schema": record.template_schema,
    }


def main() -> None:
    tenant_id = f"tenant_parity_{uuid4().hex[:10]}"
    actor_id = "parity_runner"
    template_id = f"tmpl_parity_{uuid4().hex[:8]}"
    draft_version = "1.0.0"

    initialize_template_slice(tenant_id=tenant_id, seed=False)

    sql_store = SqlAlchemyGovernancePersistenceAdapter()
    dynamo_store = DynamoDbGovernancePersistenceAdapter()

    create_payload = CreateTemplateVersionRequest(
        template_id=template_id,
        version=draft_version,
        name="Parity Template",
        description="Template parity test",
    )
    update_payload = UpdateTemplateDefinitionRequest(
        name="Parity Template",
        description="Updated by parity script",
        schema={
            "required": ["subject"],
            "properties": {
                "subject": {
                    "type": "string",
                    "title": "Subject",
                    "enum": ["Math", "Science"],
                }
            },
            "routing": {},
        },
    )

    sql_created = sql_store.create_template_version(create_payload, actor_id, tenant_id)
    dynamo_created = dynamo_store.create_template_version(create_payload, actor_id, tenant_id)

    sql_updated = sql_store.update_template_definition(template_id, draft_version, update_payload, actor_id, tenant_id)
    dynamo_updated = dynamo_store.update_template_definition(template_id, draft_version, update_payload, actor_id, tenant_id)

    sql_validation = sql_store.validate_template_definition(template_id, draft_version, tenant_id)
    dynamo_validation = dynamo_store.validate_template_definition(template_id, draft_version, tenant_id)

    sql_published = sql_store.update_template_status(template_id, draft_version, TemplateStatus.PUBLISHED, actor_id, tenant_id, None)
    dynamo_published = dynamo_store.update_template_status(template_id, draft_version, TemplateStatus.PUBLISHED, actor_id, tenant_id, None)

    sql_admin_records = sql_store.list_templates(tenant_id, include_non_published=True)
    dynamo_admin_records = dynamo_store.list_templates(tenant_id, include_non_published=True)

    result = {
        "tenant_id": tenant_id,
        "template_id": template_id,
        "checks": {
            "create_equal": _record_dict(sql_created) == _record_dict(dynamo_created),
            "update_equal": _record_dict(sql_updated) == _record_dict(dynamo_updated),
            "validation_equal": sql_validation.model_dump(mode="python") == dynamo_validation.model_dump(mode="python"),
            "publish_equal": _record_dict(sql_published) == _record_dict(dynamo_published),
            "admin_list_equal": [_record_dict(r) for r in sql_admin_records] == [_record_dict(r) for r in dynamo_admin_records],
        },
    }
    result["parity_ok"] = all(result["checks"].values())
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
