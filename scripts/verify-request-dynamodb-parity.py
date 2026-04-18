from __future__ import annotations

import json
from uuid import uuid4

from app.models.request import (
    AmendRequest,
    CancelRequest,
    CloneRequest,
    CreateRequestDraft,
    RequestPriority,
    SubmitRequest,
    SupersedeRequest,
)
from app.models.template import CreateTemplateVersionRequest, TemplateStatus, UpdateTemplateDefinitionRequest, seed_templates
from app.persistence.dynamodb_bootstrap import initialize_template_slice
from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter
from app.persistence.sql_governance_adapter import SqlAlchemyGovernancePersistenceAdapter
from app.persistence.sql_service_adapters import SqlAlchemyRequestLifecycleAdapter


def _record_shape(record):
    policy_context = json.loads(json.dumps(record.policy_context))
    routing = policy_context.get("routing")
    if isinstance(routing, dict) and routing.get("resolved_at"):
        routing["resolved_at"] = "<normalized>"
    return {
        "tenant_id": record.tenant_id,
        "request_type": record.request_type,
        "template_id": record.template_id,
        "template_version": record.template_version,
        "title": record.title,
        "summary": record.summary,
        "status": str(record.status),
        "priority": str(record.priority),
        "submitter_id": record.submitter_id,
        "owner_team_id": record.owner_team_id,
        "workflow_binding_id": record.workflow_binding_id,
        "policy_context": policy_context,
        "input_payload": record.input_payload,
        "is_archived": record.is_archived,
    }


def _ensure_template_seeded(store, actor_id: str, tenant_id: str) -> None:
    template = seed_templates()[0]
    create_payload = CreateTemplateVersionRequest(
        template_id=template.id,
        version=template.version,
        name=template.name,
        description=template.description,
    )
    update_payload = UpdateTemplateDefinitionRequest(
        name=template.name,
        description=template.description,
        schema=template.template_schema,
    )
    store.create_template_version(create_payload, actor_id, tenant_id)
    store.update_template_definition(template.id, template.version, update_payload, actor_id, tenant_id)
    store.update_template_status(template.id, template.version, TemplateStatus.PUBLISHED, actor_id, tenant_id, None)


def main() -> None:
    tenant_id = f"tenant_request_parity_{uuid4().hex[:10]}"
    actor_id = "parity_runner"
    initialize_template_slice(tenant_id=tenant_id, seed=False)

    sql_store = SqlAlchemyGovernancePersistenceAdapter()
    sql_lifecycle_store = SqlAlchemyRequestLifecycleAdapter()
    dynamo_store = DynamoDbGovernancePersistenceAdapter()

    _ensure_template_seeded(sql_store, actor_id, tenant_id)
    _ensure_template_seeded(dynamo_store, actor_id, tenant_id)

    create_payload = CreateRequestDraft(
        template_id="tmpl_curriculum",
        template_version="3.1.0",
        title="Parity Request",
        summary="Initial request for parity verification",
        priority=RequestPriority.HIGH,
        input_payload={"subject": "Math", "grade_level": "Grade 4"},
    )

    sql_created = sql_store.create_request_draft(create_payload, actor_id, tenant_id)
    dynamo_created = dynamo_store.create_request_draft(create_payload, actor_id, tenant_id)

    sql_submitted = sql_store.submit_request(sql_created.id, SubmitRequest(actor_id=actor_id, reason="Submit parity"), tenant_id)
    dynamo_submitted = dynamo_store.submit_request(dynamo_created.id, SubmitRequest(actor_id=actor_id, reason="Submit parity"), tenant_id)

    sql_amended = sql_store.amend_request(
        sql_created.id,
        AmendRequest(
            actor_id=actor_id,
            reason="Amend parity",
            summary="Updated summary",
            input_payload={"subject": "Science", "grade_level": "Grade 5"},
        ),
        tenant_id,
    )
    dynamo_amended = dynamo_store.amend_request(
        dynamo_created.id,
        AmendRequest(
            actor_id=actor_id,
            reason="Amend parity",
            summary="Updated summary",
            input_payload={"subject": "Science", "grade_level": "Grade 5"},
        ),
        tenant_id,
    )

    sql_canceled = sql_store.cancel_request(sql_created.id, CancelRequest(actor_id=actor_id, reason="Cancel parity"), tenant_id)
    dynamo_canceled = dynamo_store.cancel_request(dynamo_created.id, CancelRequest(actor_id=actor_id, reason="Cancel parity"), tenant_id)

    sql_clone = sql_store.clone_request(sql_created.id, CloneRequest(actor_id=actor_id, reason="Clone parity"), tenant_id)
    dynamo_clone = dynamo_store.clone_request(dynamo_created.id, CloneRequest(actor_id=actor_id, reason="Clone parity"), tenant_id)

    sql_supersede_target = sql_store.create_request_draft(
        create_payload.model_copy(update={"title": "Replacement Request"}),
        actor_id,
        tenant_id,
    )
    dynamo_supersede_target = dynamo_store.create_request_draft(
        create_payload.model_copy(update={"title": "Replacement Request"}),
        actor_id,
        tenant_id,
    )

    sql_superseded = sql_store.supersede_request(
        sql_clone.id,
        SupersedeRequest(actor_id=actor_id, replacement_request_id=sql_supersede_target.id, reason="Supersede parity"),
        tenant_id,
    )
    dynamo_superseded = dynamo_store.supersede_request(
        dynamo_clone.id,
        SupersedeRequest(actor_id=actor_id, replacement_request_id=dynamo_supersede_target.id, reason="Supersede parity"),
        tenant_id,
    )

    sql_history = sql_lifecycle_store.list_audit_entries(sql_clone.id, tenant_id)
    dynamo_history = dynamo_store.list_audit_entries(dynamo_clone.id, tenant_id)

    result = {
        "tenant_id": tenant_id,
        "checks": {
            "create_equal": _record_shape(sql_created) == _record_shape(dynamo_created),
            "submit_equal": _record_shape(sql_submitted) == _record_shape(dynamo_submitted),
            "amend_equal": _record_shape(sql_amended) == _record_shape(dynamo_amended),
            "cancel_equal": _record_shape(sql_canceled) == _record_shape(dynamo_canceled),
            "clone_equal": _record_shape(sql_clone) == _record_shape(dynamo_clone),
            "supersede_equal": _record_shape(sql_superseded) == _record_shape(dynamo_superseded),
            "history_action_sequence_equal": [entry.action for entry in sql_history] == [entry.action for entry in dynamo_history],
        },
    }
    result["parity_ok"] = all(result["checks"].values())
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
