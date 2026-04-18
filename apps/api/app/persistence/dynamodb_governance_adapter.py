from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import desc, select

from app.core.config import settings
from app.db.models import AgentSessionMessageTable, AgentSessionTable, ArtifactTable, CheckResultTable, CheckRunTable, IntegrationTable, PromotionTable, RequestRelationshipTable, ReviewQueueTable, RunTable
from app.db.session import SessionLocal
from app.domain import template_engine as _te
from app.models.common import PaginatedResponse
from app.models.governance import AuditEntry, CheckResult, CheckRunRecord, CheckRunStatus, InstructionalWorkflowDecisionRequest, InstructionalWorkflowProjectionRecord, RequestDetail, RequestRelationship
from app.models.request import (
    AmendRequest,
    CancelRequest,
    CloneRequest,
    CreateRequestDraft,
    RequestCheckRun,
    RequestPriority,
    RequestRecord,
    RequestStatus,
    SubmitRequest,
    SupersedeRequest,
    TransitionRequest,
)
from app.models.security import PublicRegistrationRequest, RegistrationSubmissionResponse
from app.models.template import (
    CreateTemplateVersionRequest,
    TemplateRecord,
    TemplateStatus,
    TemplateValidationResult,
    UpdateTemplateDefinitionRequest,
)
from app.persistence.contracts import RequestLifecyclePort, RequestPersistencePort, TemplatePersistencePort
from app.repositories.governance_repository import GovernanceRepository, governance_repository
from app.domain.state_machine import (
    AMENDABLE_STATUSES as _SM_AMENDABLE_STATUSES,
    CANCELABLE_STATUSES as _SM_CANCELABLE_STATUSES,
    TRANSITION_RULES as _SM_TRANSITION_RULES,
    compute_sla_risk as _sm_compute_sla_risk,
)
from app.services.policy_check_service import policy_check_service


class DynamoDbGovernancePersistenceAdapter(RequestPersistencePort, TemplatePersistencePort, RequestLifecyclePort):
    """
    DynamoDB adapter scaffold for the first governance migration slices.

    This adapter is intentionally narrow: it targets request and template
    aggregates first because those service boundaries have already been isolated
    from the SQL repositories. The current implementation provides canonical key
    builders and table access wiring, but the command/query methods remain to be
    implemented as parity-tested DynamoDB operations.
    """

    def __init__(self, table_name: str | None = None, dynamodb_resource: Any | None = None) -> None:
        self._table_name = table_name or settings.dynamodb_governance_table
        self._resource = dynamodb_resource

    @property
    def table(self) -> Any:
        if self._resource is None:
            import boto3

            self._resource = boto3.resource(
                "dynamodb",
                region_name=settings.dynamodb_region,
                endpoint_url=settings.dynamodb_endpoint_url,
            )
        return self._resource.Table(self._table_name)

    @staticmethod
    def request_pk(tenant_id: str, request_id: str) -> str:
        return f"TENANT#{tenant_id}#REQUEST#{request_id}"

    @staticmethod
    def request_root_sk() -> str:
        return "REQUEST"

    @staticmethod
    def request_event_sk(event_id: str) -> str:
        return f"EVENT#{event_id}"

    @staticmethod
    def request_check_run_sk(queued_at: str, check_run_id: str) -> str:
        return f"CHECK_RUN#{queued_at}#{check_run_id}"

    @staticmethod
    def request_relationship_sk(direction: str, request_id: str, relationship_type: str) -> str:
        return f"REL#{direction.upper()}#{request_id}#{relationship_type}"

    @staticmethod
    def template_pk(tenant_id: str, template_id: str) -> str:
        return f"TENANT#{tenant_id}#TEMPLATE#{template_id}"

    @staticmethod
    def template_version_sk(version: str) -> str:
        return f"TEMPLATE_VERSION#{version}"

    @staticmethod
    def template_current_sk() -> str:
        return "TEMPLATE_CURRENT"

    @staticmethod
    def request_current_sk() -> str:
        return "REQUEST_CURRENT"

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value)

    @staticmethod
    def _template_item_to_record(item: dict[str, Any]) -> TemplateRecord:
        return TemplateRecord.model_validate(
            {
                "id": item["id"],
                "version": item["version"],
                "name": item["name"],
                "description": item["description"],
                "status": item["status"],
                "schema": deepcopy(item.get("template_schema") or {}),
                "created_at": DynamoDbGovernancePersistenceAdapter._parse_datetime(item["created_at"]),
                "updated_at": DynamoDbGovernancePersistenceAdapter._parse_datetime(item["updated_at"]),
            }
        )

    @staticmethod
    def _request_item_to_record(item: dict[str, Any]) -> RequestRecord:
        status = item["status"]
        priority = item["priority"]
        updated_at = DynamoDbGovernancePersistenceAdapter._parse_datetime(item["updated_at"])
        sla_risk_level, sla_risk_reason = _sm_compute_sla_risk(status, priority, item.get("sla_policy_id"), updated_at)
        return RequestRecord.model_validate(
            {
                "id": item["id"],
                "tenant_id": item["tenant_id"],
                "request_type": item["request_type"],
                "template_id": item["template_id"],
                "template_version": item["template_version"],
                "title": item["title"],
                "summary": item["summary"],
                "status": status,
                "priority": priority,
                "sla_policy_id": item.get("sla_policy_id"),
                "submitter_id": item["submitter_id"],
                "owner_team_id": item.get("owner_team_id"),
                "owner_user_id": item.get("owner_user_id"),
                "workflow_binding_id": item.get("workflow_binding_id"),
                "current_run_id": item.get("current_run_id"),
                "policy_context": deepcopy(item.get("policy_context") or {}),
                "input_payload": deepcopy(item.get("input_payload") or {}),
                "tags": list(item.get("tags") or []),
                "created_at": DynamoDbGovernancePersistenceAdapter._parse_datetime(item["created_at"]),
                "created_by": item["created_by"],
                "updated_at": updated_at,
                "updated_by": item["updated_by"],
                "version": int(item["version"]),
                "is_archived": bool(item.get("is_archived", False)),
                "sla_risk_level": sla_risk_level,
                "sla_risk_reason": sla_risk_reason,
                "federated_projection_count": 0,
                "federated_conflict_count": 0,
            }
        )

    @staticmethod
    def _request_record_to_item(record: RequestRecord) -> dict[str, Any]:
        return {
            "PK": DynamoDbGovernancePersistenceAdapter.request_pk(record.tenant_id, record.id),
            "SK": DynamoDbGovernancePersistenceAdapter.request_root_sk(),
            "record_type": "request",
            "entity_type": "request",
            "id": record.id,
            "tenant_id": record.tenant_id,
            "request_type": record.request_type,
            "template_id": record.template_id,
            "template_version": record.template_version,
            "title": record.title,
            "summary": record.summary,
            "status": record.status.value if isinstance(record.status, RequestStatus) else str(record.status),
            "priority": record.priority.value if isinstance(record.priority, RequestPriority) else str(record.priority),
            "sla_policy_id": record.sla_policy_id,
            "submitter_id": record.submitter_id,
            "owner_team_id": record.owner_team_id,
            "owner_user_id": record.owner_user_id,
            "workflow_binding_id": record.workflow_binding_id,
            "current_run_id": record.current_run_id,
            "policy_context": deepcopy(record.policy_context),
            "input_payload": deepcopy(record.input_payload),
            "tags": list(record.tags),
            "created_at": record.created_at.isoformat(),
            "created_by": record.created_by,
            "updated_at": record.updated_at.isoformat(),
            "updated_by": record.updated_by,
            "version": record.version,
            "is_archived": record.is_archived,
        }

    @staticmethod
    def _template_record_to_item(record: TemplateRecord, tenant_id: str) -> dict[str, Any]:
        return {
            "PK": DynamoDbGovernancePersistenceAdapter.template_pk(tenant_id, record.id),
            "SK": DynamoDbGovernancePersistenceAdapter.template_version_sk(record.version),
            "record_type": "template_version",
            "entity_type": "template",
            "tenant_id": tenant_id,
            "id": record.id,
            "version": record.version,
            "name": record.name,
            "description": record.description,
            "status": record.status.value if isinstance(record.status, TemplateStatus) else str(record.status),
            "template_schema": deepcopy(record.template_schema),
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }

    @staticmethod
    def _validate_template_definition(template_schema: dict) -> TemplateValidationResult:
        return _te.validate_definition(template_schema)

    def _scan_items(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        kwargs: dict[str, Any] = {}
        while True:
            response = self.table.scan(**kwargs)
            items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return items
            kwargs["ExclusiveStartKey"] = last_key

    def _list_template_items(self, tenant_id: str) -> list[dict[str, Any]]:
        prefix = f"TENANT#{tenant_id}#TEMPLATE#"
        return [
            item
            for item in self._scan_items()
            if item.get("record_type") == "template_version" and str(item.get("PK", "")).startswith(prefix)
        ]

    def _get_template_item(self, tenant_id: str, template_id: str, version: str) -> dict[str, Any] | None:
        response = self.table.get_item(
            Key={
                "PK": self.template_pk(tenant_id, template_id),
                "SK": self.template_version_sk(version),
            }
        )
        item = response.get("Item")
        if item and item.get("record_type") == "template_version":
            return item
        return None

    def _list_request_items(self, tenant_id: str) -> list[dict[str, Any]]:
        prefix = f"TENANT#{tenant_id}#REQUEST#"
        return [
            item
            for item in self._scan_items()
            if item.get("record_type") == "request" and str(item.get("PK", "")).startswith(prefix)
        ]

    def _get_request_item(self, tenant_id: str, request_id: str) -> dict[str, Any] | None:
        response = self.table.get_item(
            Key={
                "PK": self.request_pk(tenant_id, request_id),
                "SK": self.request_root_sk(),
            }
        )
        item = response.get("Item")
        if item and item.get("record_type") == "request":
            return item
        return None

    def _put_request_item(self, item: dict[str, Any]) -> None:
        self.table.put_item(Item=item)

    def _put_request_event(
        self,
        *,
        tenant_id: str,
        request_id: str,
        actor_id: str,
        action: str,
        reason_or_evidence: str,
    ) -> None:
        event_id = uuid4().hex
        created_at = self._now_iso()
        self.table.put_item(
            Item={
                "PK": self.request_pk(tenant_id, request_id),
                "SK": self.request_event_sk(f"{created_at}#{event_id}"),
                "record_type": "request_event",
                "entity_type": "request",
                "request_id": request_id,
                "tenant_id": tenant_id,
                "event_id": event_id,
                "timestamp": created_at,
                "actor": actor_id,
                "action": action,
                "object_type": "request",
                "object_id": request_id,
                "reason_or_evidence": reason_or_evidence,
            }
        )
        with SessionLocal() as session:
            from app.services.event_store_service import event_store_service

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="request.event_recorded",
                aggregate_type="request",
                aggregate_id=request_id,
                request_id=request_id,
                actor=actor_id,
                detail=action,
                payload={"reason_or_evidence": reason_or_evidence},
            )
            session.commit()

    @staticmethod
    def _check_run_item_to_record(item: dict[str, Any]) -> CheckRunRecord:
        return CheckRunRecord.model_validate(
            {
                "id": item["id"],
                "request_id": item["request_id"],
                "promotion_id": item.get("promotion_id"),
                "scope": item["scope"],
                "status": item["status"],
                "trigger_reason": item["trigger_reason"],
                "enqueued_by": item["enqueued_by"],
                "worker_task_id": item.get("worker_task_id"),
                "error_message": item.get("error_message"),
                "queued_at": item["queued_at"],
                "started_at": item.get("started_at"),
                "completed_at": item.get("completed_at"),
            }
        )

    def _put_request_check_run(
        self,
        *,
        tenant_id: str,
        request_id: str,
        actor_id: str,
        reason: str,
    ) -> CheckRunRecord:
        existing_item = next(
            (
                item
                for item in self._list_request_check_run_items(tenant_id, request_id)
                if item.get("status") in {CheckRunStatus.QUEUED.value, CheckRunStatus.RUNNING.value}
            ),
            None,
        )
        if existing_item is not None:
            return self._check_run_item_to_record(existing_item)
        queued_at = self._now_iso().replace("+00:00", "Z")
        check_run_id = f"chk_{uuid4().hex[:12]}"
        item = {
            "PK": self.request_pk(tenant_id, request_id),
            "SK": self.request_check_run_sk(queued_at, check_run_id),
            "record_type": "request_check_run",
            "entity_type": "request",
            "id": check_run_id,
            "request_id": request_id,
            "tenant_id": tenant_id,
            "promotion_id": None,
            "scope": "request",
            "status": CheckRunStatus.QUEUED.value,
            "trigger_reason": reason,
            "enqueued_by": actor_id,
            "worker_task_id": None,
            "error_message": None,
            "queued_at": queued_at,
            "started_at": None,
            "completed_at": None,
        }
        self.table.put_item(Item=item)
        with SessionLocal() as session:
            from app.services.event_store_service import event_store_service
            from app.services.check_dispatch_service import check_dispatch_service

            if session.get(CheckRunTable, check_run_id) is None:
                session.add(
                    CheckRunTable(
                        id=check_run_id,
                        request_id=request_id,
                        promotion_id=None,
                        scope="request",
                        status=CheckRunStatus.QUEUED.value,
                        trigger_reason=reason,
                        enqueued_by=actor_id,
                        worker_task_id=None,
                        error_message=None,
                        queued_at=self._parse_datetime(queued_at),
                        started_at=None,
                        completed_at=None,
                    )
                )
                session.flush()
                event_store_service.append(
                    session,
                    tenant_id=tenant_id,
                    event_type="check_run.enqueued",
                    aggregate_type="check_run",
                    aggregate_id=check_run_id,
                    request_id=request_id,
                    check_run_id=check_run_id,
                    actor=actor_id,
                    detail=reason,
                    payload={"scope": "request"},
                )
                check_dispatch_service._dispatch(session, check_run_id)
            session.commit()
        return self._check_run_item_to_record(item)

    def _get_request_check_run_item(self, check_run_id: str) -> dict[str, Any] | None:
        return next(
            (
                item
                for item in self._scan_items()
                if item.get("record_type") == "request_check_run" and item.get("id") == check_run_id
            ),
            None,
        )

    def _update_request_check_run_item(
        self,
        check_run_id: str,
        *,
        status: str,
        worker_task_id: str | None = None,
        error_message: str | None = None,
        started_at: str | None = None,
        completed_at: str | None = None,
    ) -> None:
        item = self._get_request_check_run_item(check_run_id)
        if item is None:
            return
        updated = {
            **item,
            "status": status,
            "worker_task_id": worker_task_id if worker_task_id is not None else item.get("worker_task_id"),
            "error_message": error_message,
            "started_at": started_at if started_at is not None else item.get("started_at"),
            "completed_at": completed_at if completed_at is not None else item.get("completed_at"),
        }
        self.table.put_item(Item=updated)

    def _list_request_check_run_items(self, tenant_id: str, request_id: str) -> list[dict[str, Any]]:
        prefix = self.request_pk(tenant_id, request_id)
        items = [
            item
            for item in self._scan_items()
            if item.get("record_type") == "request_check_run" and item.get("PK") == prefix
        ]
        items.sort(key=lambda item: item["queued_at"], reverse=True)
        return items

    def _put_request_relationship(
        self,
        *,
        tenant_id: str,
        source_request_id: str,
        target_request_id: str,
        relationship_type: str,
        actor_id: str,
    ) -> None:
        created_at = self._now_iso().replace("+00:00", "Z")
        for direction, related_request_id in (("source", target_request_id), ("target", source_request_id)):
            self.table.put_item(
                Item={
                    "PK": self.request_pk(tenant_id, source_request_id if direction == "source" else target_request_id),
                    "SK": self.request_relationship_sk(direction, related_request_id, relationship_type),
                    "record_type": "request_relationship",
                    "entity_type": "request",
                    "tenant_id": tenant_id,
                    "source_request_id": source_request_id,
                    "target_request_id": target_request_id,
                    "relationship_type": relationship_type,
                    "direction": direction,
                    "related_request_id": related_request_id,
                    "actor_id": actor_id,
                    "created_at": created_at,
                }
            )

    def _list_request_relationships(self, tenant_id: str, request_id: str, direction: str) -> list[RequestRelationship]:
        prefix = self.request_pk(tenant_id, request_id)
        items = [
            item
            for item in self._scan_items()
            if item.get("record_type") == "request_relationship"
            and item.get("PK") == prefix
            and item.get("direction") == direction
        ]
        items.sort(key=lambda item: item["created_at"])
        return [
            RequestRelationship(
                request_id=item["related_request_id"],
                relationship_type=item["relationship_type"],
            )
            for item in items
        ]

    @staticmethod
    def _request_detail(record: RequestRecord) -> RequestDetail:
        return RequestDetail(
            request=record,
            latest_run_id=record.current_run_id,
            latest_artifact_ids=[],
            active_blockers=[],
            check_results=[],
            check_runs=[],
            agent_sessions=[],
            next_required_action=governance_repository._next_action_for_request(record.status, False, False),
            predecessors=[],
            successors=[],
        )

    @staticmethod
    def _check_result_from_sql_row(row: Any) -> CheckResult:
        return CheckResult.model_validate(
            {
                "id": row.id,
                "request_id": row.request_id,
                "promotion_id": row.promotion_id,
                "name": row.name,
                "state": row.state,
                "detail": row.detail,
                "severity": row.severity,
                "evidence": row.evidence,
                "evaluated_at": row.evaluated_at.isoformat().replace("+00:00", "Z"),
                "evaluated_by": row.evaluated_by,
            }
        )

    def _load_sql_request_detail_support(self, request_id: str) -> dict[str, Any]:
        with SessionLocal() as session:
            run_row = session.scalars(select(RunTable).where(RunTable.request_id == request_id).order_by(desc(RunTable.updated_at))).first()
            artifact_rows = session.scalars(select(ArtifactTable).where(ArtifactTable.request_id == request_id).order_by(desc(ArtifactTable.updated_at))).all()
            review_rows = session.scalars(select(ReviewQueueTable).where(ReviewQueueTable.request_id == request_id)).all()
            promotion_row = session.scalars(select(PromotionTable).where(PromotionTable.request_id == request_id).order_by(desc(PromotionTable.id))).first()
            check_rows = session.scalars(
                select(CheckResultTable).where(CheckResultTable.request_id == request_id, CheckResultTable.promotion_id.is_(None)).order_by(CheckResultTable.name)
            ).all()
            check_run_rows = session.scalars(
                select(CheckRunTable).where(CheckRunTable.request_id == request_id).order_by(desc(CheckRunTable.queued_at))
            ).all()
            predecessor_rows = session.scalars(
                select(RequestRelationshipTable).where(RequestRelationshipTable.target_request_id == request_id).order_by(RequestRelationshipTable.created_at)
            ).all()
            successor_rows = session.scalars(
                select(RequestRelationshipTable).where(RequestRelationshipTable.source_request_id == request_id).order_by(RequestRelationshipTable.created_at)
            ).all()
            agent_session_rows = session.scalars(
                select(AgentSessionTable).where(AgentSessionTable.request_id == request_id).order_by(desc(AgentSessionTable.updated_at))
            ).all()
            agent_messages = (
                session.scalars(
                    select(AgentSessionMessageTable)
                    .where(AgentSessionMessageTable.request_id == request_id)
                    .order_by(AgentSessionMessageTable.created_at)
                ).all()
                if agent_session_rows
                else []
            )
            integration_rows = {
                row.id: row
                for row in session.scalars(
                    select(IntegrationTable).where(
                        IntegrationTable.id.in_([item.integration_id for item in agent_session_rows])
                    )
                ).all()
            } if agent_session_rows else {}
        return {
            "run_row": run_row,
            "artifact_rows": artifact_rows,
            "review_rows": review_rows,
            "promotion_row": promotion_row,
            "check_rows": check_rows,
            "check_run_rows": check_run_rows,
            "predecessor_rows": predecessor_rows,
            "successor_rows": successor_rows,
            "agent_session_rows": agent_session_rows,
            "agent_messages": agent_messages,
            "integration_rows": integration_rows,
        }

    @staticmethod
    def _next_request_id() -> str:
        return f"req_{uuid4().hex[:12]}"

    def _put_template_item(self, item: dict[str, Any]) -> None:
        self.table.put_item(Item=item)

    def _put_template_event(
        self,
        *,
        tenant_id: str,
        template_id: str,
        version: str,
        actor_id: str,
        event_type: str,
        detail: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        event_id = uuid4().hex
        created_at = self._now_iso()
        self.table.put_item(
            Item={
                "PK": self.template_pk(tenant_id, template_id),
                "SK": self.request_event_sk(f"{created_at}#{event_id}"),
                "record_type": "template_event",
                "entity_type": "template",
                "tenant_id": tenant_id,
                "template_id": template_id,
                "template_version": version,
                "event_id": event_id,
                "event_type": event_type,
                "detail": detail,
                "actor_id": actor_id,
                "payload": payload or {},
                "created_at": created_at,
            }
        )

    def _refresh_template_current(self, tenant_id: str, template_id: str) -> None:
        versions = [item for item in self._list_template_items(tenant_id) if item["id"] == template_id]
        current_key = {
            "PK": self.template_pk(tenant_id, template_id),
            "SK": self.template_current_sk(),
        }
        if not versions:
            self.table.delete_item(Key=current_key)
            return
        versions.sort(key=lambda item: (item["updated_at"], item["version"]))
        latest = versions[-1]
        published = [item for item in versions if item["status"] == TemplateStatus.PUBLISHED.value]
        current_item = {
            **current_key,
            "record_type": "template_current",
            "entity_type": "template",
            "tenant_id": tenant_id,
            "id": template_id,
            "latest_version": latest["version"],
            "latest_status": latest["status"],
            "published_version": published[-1]["version"] if published else None,
            "updated_at": self._now_iso(),
        }
        self.table.put_item(Item=current_item)

    def list_requests(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
        owner_team_id: str | None = None,
        workflow: str | None = None,
        request_id: str | None = None,
        federation: str | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[RequestRecord]:
        request_items = self._list_request_items(tenant_id) if tenant_id else [item for item in self._scan_items() if item.get("record_type") == "request"]
        if request_id:
            request_items = [item for item in request_items if item.get("id") == request_id]
        if status:
            request_items = [item for item in request_items if item.get("status") == status]
        if owner_team_id:
            request_items = [item for item in request_items if item.get("owner_team_id") == owner_team_id]
        if workflow:
            request_items = [
                item
                for item in request_items
                if item.get("workflow_binding_id") == workflow or item.get("template_id") == workflow
            ]
        records = [self._request_item_to_record(item) for item in request_items]
        if federation == "with_projection":
            records = [record for record in records if record.federated_projection_count > 0]
        elif federation == "with_conflict":
            records = [record for record in records if record.federated_conflict_count > 0]
        records.sort(key=lambda record: record.updated_at, reverse=True)
        return PaginatedResponse.create(items=records, page=page, page_size=page_size, total_count=len(records))

    def create_request_draft(self, payload: CreateRequestDraft, actor_id: str, tenant_id: str) -> RequestRecord:
        template_item = self._get_template_item(tenant_id, payload.template_id, payload.template_version)
        if template_item is None:
            raise ValueError(f"Template {payload.template_id}@{payload.template_version} is not available for tenant {tenant_id}")
        normalized_input_payload = _te.validate_payload(
            template_item.get("template_schema") or {},
            payload.input_payload,
            require_required=False,
        )
        now = datetime.now(timezone.utc)
        record = RequestRecord(
            id=self._next_request_id(),
            tenant_id=tenant_id,
            request_type="custom",
            template_id=payload.template_id,
            template_version=payload.template_version,
            title=payload.title,
            summary=payload.summary,
            status=RequestStatus.DRAFT,
            priority=payload.priority,
            submitter_id=actor_id,
            policy_context={},
            input_payload=normalized_input_payload,
            tags=[],
            created_at=now,
            created_by=actor_id,
            updated_at=now,
            updated_by=actor_id,
            version=1,
            is_archived=False,
        )
        self._put_request_item(self._request_record_to_item(record))
        self._put_request_event(
            tenant_id=tenant_id,
            request_id=record.id,
            actor_id=actor_id,
            action="Draft Created",
            reason_or_evidence="Initial draft created through API",
        )
        return record

    def submit_request(self, request_id: str, payload: SubmitRequest, tenant_id: str) -> RequestRecord:
        item = self._get_request_item(tenant_id, request_id)
        if item is None:
            raise StopIteration(request_id)
        template_item = self._get_template_item(tenant_id, item["template_id"], item["template_version"])
        if template_item is None:
            raise ValueError(f"Bound template {item['template_id']}@{item['template_version']} is no longer available")
        current_status = RequestStatus(item["status"])
        if current_status not in GovernanceRepository.SUBMITTABLE_STATUSES:
            raise ValueError(f"Request {request_id} cannot be submitted from status {item['status']}")
        normalized_input_payload = _te.validate_payload(
            template_item.get("template_schema") or {},
            item.get("input_payload") or {},
            require_required=True,
        )
        routing = _te.resolve_routing(template_item.get("template_schema") or {}, normalized_input_payload)
        record = self._request_item_to_record(item).model_copy(
            update={
                "status": RequestStatus.SUBMITTED,
                "input_payload": normalized_input_payload,
                "owner_team_id": routing["owner_team_id"] or item.get("owner_team_id"),
                "workflow_binding_id": routing["workflow_binding_id"] or item.get("workflow_binding_id"),
                "policy_context": {
                    **dict(item.get("policy_context") or {}),
                    "routing": {
                        "resolved_at": self._now_iso().replace("+00:00", "Z"),
                        "owner_team_id": routing["owner_team_id"] or item.get("owner_team_id"),
                        "workflow_binding_id": routing["workflow_binding_id"] or item.get("workflow_binding_id"),
                        "reviewers": routing["reviewers"],
                        "promotion_approvers": routing["promotion_approvers"],
                    },
                },
                "updated_at": datetime.now(timezone.utc),
                "updated_by": payload.actor_id,
                "version": int(item["version"]) + 1,
            }
        )
        self._put_request_item(self._request_record_to_item(record))
        self._put_request_event(
            tenant_id=tenant_id,
            request_id=request_id,
            actor_id=payload.actor_id,
            action="Submitted",
            reason_or_evidence=payload.reason,
        )
        self._put_request_check_run(
            tenant_id=tenant_id,
            request_id=request_id,
            actor_id=payload.actor_id,
            reason=payload.reason,
        )
        self._put_request_event(
            tenant_id=tenant_id,
            request_id=request_id,
            actor_id=payload.actor_id,
            action="Routing Resolved",
            reason_or_evidence=f"owner_team={record.owner_team_id or 'unassigned'} workflow_binding={record.workflow_binding_id or 'unassigned'} reviewers={', '.join(routing['reviewers']) or 'none'}",
        )
        return record

    def amend_request(self, request_id: str, payload: AmendRequest, tenant_id: str) -> RequestRecord:
        item = self._get_request_item(tenant_id, request_id)
        if item is None:
            raise StopIteration(request_id)
        current_status = RequestStatus(item["status"])
        if current_status not in _SM_AMENDABLE_STATUSES:
            raise ValueError(f"Request {request_id} cannot be amended from status {item['status']}")
        record = self._request_item_to_record(item).model_copy(
            update={
                "title": payload.title if payload.title is not None else item["title"],
                "summary": payload.summary if payload.summary is not None else item["summary"],
                "priority": payload.priority if payload.priority is not None else RequestPriority(item["priority"]),
                "input_payload": payload.input_payload if payload.input_payload is not None else deepcopy(item.get("input_payload") or {}),
                "status": RequestStatus.DRAFT,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": payload.actor_id,
                "version": int(item["version"]) + 1,
            }
        )
        self._put_request_item(self._request_record_to_item(record))
        self._put_request_event(
            tenant_id=tenant_id,
            request_id=request_id,
            actor_id=payload.actor_id,
            action="Amended",
            reason_or_evidence=payload.reason,
        )
        return record

    def cancel_request(self, request_id: str, payload: CancelRequest, tenant_id: str) -> RequestRecord:
        item = self._get_request_item(tenant_id, request_id)
        if item is None:
            raise StopIteration(request_id)
        current_status = RequestStatus(item["status"])
        if current_status not in _SM_CANCELABLE_STATUSES:
            raise ValueError(f"Request {request_id} cannot be canceled from status {item['status']}")
        record = self._request_item_to_record(item).model_copy(
            update={
                "status": RequestStatus.CANCELED,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": payload.actor_id,
                "version": int(item["version"]) + 1,
            }
        )
        self._put_request_item(self._request_record_to_item(record))
        self._put_request_event(
            tenant_id=tenant_id,
            request_id=request_id,
            actor_id=payload.actor_id,
            action="Canceled",
            reason_or_evidence=payload.reason,
        )
        return record

    def transition_request(self, request_id: str, payload: TransitionRequest, tenant_id: str) -> RequestRecord:
        item = self._get_request_item(tenant_id, request_id)
        if item is None:
            raise StopIteration(request_id)
        current_status = RequestStatus(item["status"])
        target_status = payload.target_status
        if target_status in {RequestStatus.DRAFT, RequestStatus.SUBMITTED, RequestStatus.CANCELED, RequestStatus.ARCHIVED}:
            raise ValueError(f"Use the dedicated mutation for target status {target_status.value}")
        allowed_targets = _SM_TRANSITION_RULES.get(current_status, set())
        if target_status not in allowed_targets:
            raise ValueError(f"Request {request_id} cannot transition from {item['status']} to {target_status.value}")
        with SessionLocal() as session:
            required_checks = policy_check_service.active_transition_gate_check_names(session, target_status, tenant_id)
            if required_checks:
                pending_check_runs = [
                    check_run
                    for check_run in self._list_request_check_run_items(tenant_id, request_id)
                    if check_run.get("status") in {CheckRunStatus.QUEUED.value, CheckRunStatus.RUNNING.value}
                ]
                if pending_check_runs:
                    raise ValueError(f"Request checks are still queued or running for {request_id}. Retry the transition after they complete")
                try:
                    policy_check_service.assert_request_transition_ready(session, request_id, target_status, tenant_id)
                except ValueError as exc:
                    self._put_request_check_run(
                        tenant_id=tenant_id,
                        request_id=request_id,
                        actor_id=payload.actor_id,
                        reason=f"Transition preflight for {target_status.value}",
                    )
                    raise ValueError(f"{exc}. Automated evaluation queued") from exc
        record = self._request_item_to_record(item).model_copy(
            update={
                "status": target_status,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": payload.actor_id,
                "version": int(item["version"]) + 1,
            }
        )
        with SessionLocal() as session:
            governance_repository._apply_transition_side_effects(session, record, current_status, target_status, payload.actor_id)
            session.commit()
        self._put_request_item(self._request_record_to_item(record))
        self._put_request_event(
            tenant_id=tenant_id,
            request_id=request_id,
            actor_id=payload.actor_id,
            action=f"Transitioned to {target_status.value}",
            reason_or_evidence=payload.reason,
        )
        return record

    def clone_request(self, request_id: str, payload: CloneRequest, tenant_id: str) -> RequestRecord:
        item = self._get_request_item(tenant_id, request_id)
        if item is None:
            raise StopIteration(request_id)
        source_record = self._request_item_to_record(item)
        now = datetime.now(timezone.utc)
        cloned_record = source_record.model_copy(
            update={
                "id": self._next_request_id(),
                "title": payload.title or f"{source_record.title} (Clone)",
                "summary": payload.summary or source_record.summary,
                "status": RequestStatus.DRAFT,
                "submitter_id": payload.actor_id,
                "current_run_id": None,
                "created_at": now,
                "created_by": payload.actor_id,
                "updated_at": now,
                "updated_by": payload.actor_id,
                "version": 1,
                "is_archived": False,
            }
        )
        self._put_request_item(self._request_record_to_item(cloned_record))
        self._put_request_event(
            tenant_id=tenant_id,
            request_id=request_id,
            actor_id=payload.actor_id,
            action="Cloned",
            reason_or_evidence=f"{payload.reason}. Replacement draft: {cloned_record.id}",
        )
        self._put_request_relationship(
            tenant_id=tenant_id,
            source_request_id=request_id,
            target_request_id=cloned_record.id,
            relationship_type="clone",
            actor_id=payload.actor_id,
        )
        self._put_request_event(
            tenant_id=tenant_id,
            request_id=cloned_record.id,
            actor_id=payload.actor_id,
            action="Draft Created",
            reason_or_evidence=f"Cloned from request {request_id}",
        )
        return cloned_record

    def supersede_request(self, request_id: str, payload: SupersedeRequest, tenant_id: str) -> RequestRecord:
        item = self._get_request_item(tenant_id, request_id)
        replacement_item = self._get_request_item(tenant_id, payload.replacement_request_id)
        if item is None:
            raise StopIteration(request_id)
        if replacement_item is None:
            raise StopIteration(payload.replacement_request_id)
        if request_id == payload.replacement_request_id:
            raise ValueError("Replacement request must differ from the request being superseded")
        if item["status"] in {RequestStatus.ARCHIVED.value, RequestStatus.CANCELED.value, RequestStatus.COMPLETED.value}:
            raise ValueError(f"Request {request_id} cannot be superseded from status {item['status']}")
        record = self._request_item_to_record(item).model_copy(
            update={
                "status": RequestStatus.ARCHIVED,
                "is_archived": True,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": payload.actor_id,
                "version": int(item["version"]) + 1,
            }
        )
        self._put_request_item(self._request_record_to_item(record))
        self._put_request_event(
            tenant_id=tenant_id,
            request_id=request_id,
            actor_id=payload.actor_id,
            action="Superseded",
            reason_or_evidence=f"{payload.reason}. Replacement request: {payload.replacement_request_id}",
        )
        self._put_request_relationship(
            tenant_id=tenant_id,
            source_request_id=request_id,
            target_request_id=payload.replacement_request_id,
            relationship_type="supersedes",
            actor_id=payload.actor_id,
        )
        self._put_request_event(
            tenant_id=tenant_id,
            request_id=payload.replacement_request_id,
            actor_id=payload.actor_id,
            action="Superseding Request Linked",
            reason_or_evidence=f"Supersedes request {request_id}",
        )
        return record

    def run_request_checks(self, request_id: str, payload: RequestCheckRun, tenant_id: str) -> RequestRecord:
        item = self._get_request_item(tenant_id, request_id)
        if item is None:
            raise StopIteration(request_id)
        self._put_request_check_run(
            tenant_id=tenant_id,
            request_id=request_id,
            actor_id=payload.actor_id,
            reason=payload.reason,
        )
        self._put_request_event(
            tenant_id=tenant_id,
            request_id=request_id,
            actor_id=payload.actor_id,
            action="Request Checks Queued",
            reason_or_evidence=payload.reason,
        )
        return self._request_item_to_record(item)

    def list_templates(self, tenant_id: str, include_non_published: bool = False) -> list[TemplateRecord]:
        items = self._list_template_items(tenant_id)
        records = [self._template_item_to_record(item) for item in items]
        if not include_non_published:
            records = [record for record in records if record.status == TemplateStatus.PUBLISHED]
        return sorted(records, key=lambda record: (record.id, record.version))

    def create_template_version(self, payload: CreateTemplateVersionRequest, actor_id: str, tenant_id: str) -> TemplateRecord:
        template_id = payload.template_id.strip()
        version = payload.version.strip()
        if not template_id:
            raise ValueError("Template id is required")
        if not version:
            raise ValueError("Template version is required")
        if self._get_template_item(tenant_id, template_id, version) is not None:
            raise ValueError(f"Template version {template_id}@{version} already exists")
        source_item = None
        versions = [item for item in self._list_template_items(tenant_id) if item["id"] == template_id]
        if payload.source_version:
            source_item = self._get_template_item(tenant_id, template_id, payload.source_version)
            if source_item is None:
                raise StopIteration(f"{template_id}@{payload.source_version}")
        elif versions:
            versions.sort(key=lambda item: (item["created_at"], item["version"]))
            source_item = versions[-1]
        now = datetime.now(timezone.utc)
        record = TemplateRecord(
            id=template_id,
            version=version,
            name=payload.name or (source_item["name"] if source_item else template_id.replace("tmpl_", "").replace("_", " ").title()),
            description=payload.description or (source_item["description"] if source_item else f"Draft template for {template_id}."),
            status=TemplateStatus.DRAFT,
            schema=deepcopy(source_item.get("template_schema") if source_item else {"required": [], "properties": {}, "routing": {}}),
            created_at=now,
            updated_at=now,
        )
        self._put_template_item(self._template_record_to_item(record, tenant_id))
        self._put_template_event(
            tenant_id=tenant_id,
            template_id=template_id,
            version=version,
            actor_id=actor_id,
            event_type="template.version_created",
            detail=f"Created draft template version {template_id}@{version}",
            payload={"template_id": template_id, "template_version": version, "source_version": payload.source_version},
        )
        self._refresh_template_current(tenant_id, template_id)
        return record

    def get_request(self, request_id: str, tenant_id: str | None = None) -> RequestDetail:
        if tenant_id is None:
            request_items = [item for item in self._scan_items() if item.get("record_type") == "request" and item.get("id") == request_id]
            if not request_items:
                raise StopIteration(request_id)
            item = request_items[0]
            tenant_id = item["tenant_id"]
        else:
            item = self._get_request_item(tenant_id, request_id)
            if item is None:
                raise StopIteration(request_id)
        record = self._request_item_to_record(item)
        sql_support = self._load_sql_request_detail_support(request_id)
        check_runs = [self._check_run_item_to_record(check_run) for check_run in self._list_request_check_run_items(tenant_id, request_id)]
        if not check_runs and sql_support["check_run_rows"]:
            check_runs = [governance_repository._check_run_from_row(row) for row in sql_support["check_run_rows"]]
        include_review_blockers = record.status in {
            RequestStatus.AWAITING_REVIEW,
            RequestStatus.UNDER_REVIEW,
            RequestStatus.CHANGES_REQUESTED,
        }
        blockers = [row.blocking_status for row in sql_support["review_rows"] if row.blocking_status] if include_review_blockers else []
        blockers.extend([f"{check.name}: {check.detail}" for check in sql_support["check_rows"] if check.state != "passed"])
        blockers.extend(
            [f"Checks {run.status}: {run.trigger_reason}" for run in check_runs if run.scope == "request" and run.status in {CheckRunStatus.QUEUED.value, CheckRunStatus.RUNNING.value}]
        )
        if record.status == RequestStatus.CHANGES_REQUESTED:
            blockers.append("Reviewer requested changes before progress can continue.")
        if record.status == RequestStatus.PROMOTION_PENDING and sql_support["promotion_row"] is not None:
            blockers.append(sql_support["promotion_row"].execution_readiness)
        elif record.status == RequestStatus.PROMOTION_PENDING:
            blockers.append("Promotion authorization still pending.")
        detail = self._request_detail(record)
        run_row = sql_support["run_row"]
        artifact_rows = sql_support["artifact_rows"]
        detail.latest_run_id = run_row.id if run_row else None
        detail.latest_artifact_ids = [row.id for row in artifact_rows]
        detail.check_runs = check_runs
        detail.check_results = [self._check_result_from_sql_row(row) for row in sql_support["check_rows"]]
        detail.active_blockers = blockers
        detail.predecessors = self._list_request_relationships(tenant_id, request_id, "target") or [
            governance_repository._relationship_from_predecessor_row(row) for row in sql_support["predecessor_rows"]
        ]
        detail.successors = self._list_request_relationships(tenant_id, request_id, "source") or [
            governance_repository._relationship_from_successor_row(row) for row in sql_support["successor_rows"]
        ]
        messages_by_session: dict[str, list[Any]] = {}
        for message in sql_support["agent_messages"]:
            messages_by_session.setdefault(message.session_id, []).append(message)
        detail.agent_sessions = [
            governance_repository._agent_session_from_row(
                row,
                sql_support["integration_rows"].get(row.integration_id),
                messages_by_session.get(row.id, []),
            )
            for row in sql_support["agent_session_rows"]
        ]
        if any(session.awaiting_human and session.status in {"active", "waiting_on_human"} for session in detail.agent_sessions):
            waiting_session = next(
                session for session in detail.agent_sessions if session.awaiting_human and session.status in {"active", "waiting_on_human"}
            )
            detail.active_blockers.append(f"Agent session waiting for human input: {waiting_session.agent_label}")
        detail.next_required_action = governance_repository._next_action_for_request(
            record.status,
            run_row is not None,
            sql_support["promotion_row"] is not None,
        )
        return detail

    def create_public_registration_request(self, payload: PublicRegistrationRequest) -> RegistrationSubmissionResponse:
        raise NotImplementedError("Public registration is not implemented for the DynamoDB request slice yet")

    def list_audit_entries(self, request_id: str, tenant_id: str | None = None) -> list[AuditEntry]:
        if tenant_id is None:
            request_items = [item for item in self._scan_items() if item.get("record_type") == "request" and item.get("id") == request_id]
            if not request_items:
                raise StopIteration(request_id)
            tenant_id = request_items[0]["tenant_id"]
        if self._get_request_item(tenant_id, request_id) is None:
            raise StopIteration(request_id)
        items = self._scan_items()
        prefix = self.request_pk(tenant_id, request_id)
        event_items = [
            item for item in items
            if item.get("record_type") == "request_event" and item.get("PK") == prefix
        ]
        event_items.sort(key=lambda item: item["timestamp"])
        return [
            AuditEntry(
                timestamp=item["timestamp"],
                actor=item["actor"],
                action=item["action"],
                object_type=item["object_type"],
                object_id=item["object_id"],
                reason_or_evidence=item["reason_or_evidence"],
                event_class="canonical",
                source_system="RGP",
                related_entity_type="request",
                related_entity_id=request_id,
                lineage=[f"request:{request_id}", f"{item['object_type']}:{item['object_id']}"],
            )
            for item in event_items
        ]

    def list_request_check_runs(self, request_id: str, tenant_id: str | None = None) -> list[CheckRunRecord]:
        if tenant_id is None:
            request_items = [item for item in self._scan_items() if item.get("record_type") == "request" and item.get("id") == request_id]
            if not request_items:
                raise StopIteration(request_id)
            tenant_id = request_items[0]["tenant_id"]
        elif self._get_request_item(tenant_id, request_id) is None:
            raise StopIteration(request_id)
        return [self._check_run_item_to_record(item) for item in self._list_request_check_run_items(tenant_id, request_id)]

    def list_instructional_workflow_projections(
        self,
        page: int,
        page_size: int,
        tenant_id: str | None = None,
        flightos_content_entry_id: str | None = None,
        template_id: str | None = None,
        workflow_status: str | None = None,
    ) -> PaginatedResponse[InstructionalWorkflowProjectionRecord]:
        raise NotImplementedError("Instructional workflow projections are not yet implemented for the DynamoDB governance backend.")

    def get_instructional_workflow_projection(self, request_id: str, tenant_id: str | None = None) -> InstructionalWorkflowProjectionRecord:
        raise NotImplementedError("Instructional workflow projections are not yet implemented for the DynamoDB governance backend.")

    def decide_instructional_workflow_stage(
        self,
        request_id: str,
        payload: InstructionalWorkflowDecisionRequest,
        tenant_id: str,
    ) -> InstructionalWorkflowProjectionRecord:
        raise NotImplementedError("Instructional workflow stage decisions are not yet implemented for the DynamoDB governance backend.")

    def update_template_definition(
        self,
        template_id: str,
        version: str,
        payload: UpdateTemplateDefinitionRequest,
        actor_id: str,
        tenant_id: str,
    ) -> TemplateRecord:
        item = self._get_template_item(tenant_id, template_id, version)
        if item is None:
            raise StopIteration(f"{template_id}@{version}")
        if item["status"] != TemplateStatus.DRAFT.value:
            raise ValueError("Only draft template versions can be edited")
        validation = self._validate_template_definition(payload.template_schema)
        errors = [issue for issue in validation.issues if issue.level == "error"]
        if errors:
            raise ValueError("; ".join(f"{issue.path}: {issue.message}" for issue in errors))
        record = self._template_item_to_record(item)
        record = record.model_copy(
            update={
                "name": payload.name,
                "description": payload.description,
                "template_schema": deepcopy(payload.template_schema),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._put_template_item(self._template_record_to_item(record, tenant_id))
        self._put_template_event(
            tenant_id=tenant_id,
            template_id=template_id,
            version=version,
            actor_id=actor_id,
            event_type="template.definition_updated",
            detail=f"Updated template definition for {template_id}@{version}",
            payload={"template_id": template_id, "template_version": version},
        )
        self._refresh_template_current(tenant_id, template_id)
        return record

    def validate_template_definition(self, template_id: str, version: str, tenant_id: str) -> TemplateValidationResult:
        item = self._get_template_item(tenant_id, template_id, version)
        if item is None:
            raise StopIteration(f"{template_id}@{version}")
        return self._validate_template_definition(item.get("template_schema") or {})

    def delete_template_version(self, template_id: str, version: str, actor_id: str, tenant_id: str) -> None:
        item = self._get_template_item(tenant_id, template_id, version)
        if item is None:
            raise StopIteration(f"{template_id}@{version}")
        if item["status"] != TemplateStatus.DRAFT.value:
            raise ValueError("Only draft template versions can be deleted")
        self.table.delete_item(
            Key={
                "PK": self.template_pk(tenant_id, template_id),
                "SK": self.template_version_sk(version),
            }
        )
        self._put_template_event(
            tenant_id=tenant_id,
            template_id=template_id,
            version=version,
            actor_id=actor_id,
            event_type="template.version_deleted",
            detail=f"Deleted draft template version {template_id}@{version}",
            payload={"template_id": template_id, "template_version": version},
        )
        self._refresh_template_current(tenant_id, template_id)

    def update_template_status(
        self,
        template_id: str,
        version: str,
        status: TemplateStatus,
        actor_id: str,
        tenant_id: str,
        note: str | None,
    ) -> TemplateRecord:
        item = self._get_template_item(tenant_id, template_id, version)
        if item is None:
            raise StopIteration(f"{template_id}@{version}")
        now = datetime.now(timezone.utc)
        if status == TemplateStatus.PUBLISHED:
            for published_item in self._list_template_items(tenant_id):
                if published_item["id"] != template_id:
                    continue
                if published_item["version"] == version:
                    continue
                if published_item["status"] != TemplateStatus.PUBLISHED.value:
                    continue
                deprecated_record = self._template_item_to_record(published_item).model_copy(
                    update={"status": TemplateStatus.DEPRECATED, "updated_at": now}
                )
                self._put_template_item(self._template_record_to_item(deprecated_record, tenant_id))
        record = self._template_item_to_record(item).model_copy(update={"status": status, "updated_at": now})
        self._put_template_item(self._template_record_to_item(record, tenant_id))
        self._put_template_event(
            tenant_id=tenant_id,
            template_id=template_id,
            version=version,
            actor_id=actor_id,
            event_type=f"template.{status.value}",
            detail=f"Marked template {template_id}@{version} as {status.value}",
            payload={"template_id": template_id, "template_version": version, "note": note or ""},
        )
        self._refresh_template_current(tenant_id, template_id)
        return record
