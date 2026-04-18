from copy import deepcopy
from datetime import datetime, timedelta, timezone
import re
import threading
import time
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import desc, func, select, update

from app.core.config import settings
from app.db.models import AgentSessionMessageTable, AgentSessionTable, ArtifactEventTable, ArtifactLineageEdgeTable, ArtifactTable, CapabilityTable, CheckOverrideTable, CheckResultTable, CheckRunTable, ContextAccessLogTable, ContextBundleTable, DeploymentExecutionTable, EventOutboxTable, EventStoreTable, IntegrationTable, OrganizationTable, PolicyTable, PortfolioScopeTable, PortfolioTable, ProjectionMappingTable, PromotionTable, ReconciliationLogTable, RequestEventTable, RequestRelationshipTable, RequestTable, ReviewQueueTable, RunTable, RuntimeDispatchTable, RuntimeSignalTable, TeamMembershipTable, TeamTable, TemplateTable, TenantTable, TransitionGateTable, UserTable
from app.db.session import SessionLocal
from app.domain.mcp.access_control import _mode_satisfies, filter_tools_by_policy
from app.domain.mcp.registry import mcp_tool_registry
from app.models.common import PaginatedResponse
from app.models.context import ContextAccessLogRecord, ContextBundleRecord
from app.models.security import Principal, PrincipalRole, PublicRegistrationRequest, RegistrationSubmissionResponse
from app.models.governance import (
    AnalyticsAgentRow,
    AgentSessionContextDetail,
    AgentSessionDetail,
    AgentSessionMessageCreateRequest,
    AgentSessionMessageRecord,
    AgentSessionRecord,
    AgentSessionToolRecord,
    AnalyticsBottleneckRow,
    AnalyticsWorkflowRow,
    AgentTrendPoint,
    AssignAgentSessionRequest,
    ApproveAgentSessionCheckpointRequest,
    GovernedRuntimeSummary,
    ImportAgentSessionArtifactRequest,
    ArtifactDetail,
    ArtifactEvent,
    ArtifactLineageEdge,
    ArtifactRecord,
    AuditEntry,
    CapabilityDetail,
    CapabilityRecord,
    CheckOverride,
    CheckOverrideRequest,
    CheckRunRecord,
    CheckRunRequest,
    CheckResult,
    CompleteAgentSessionRequest,
    CreateIntegrationRequest,
    CheckEvaluationRequest,
    CreateOrganizationRequest,
    CreatePortfolioRequest,
    CreateTenantRequest,
    CreateTeamRequest,
    CreateUserRequest,
    IntegrationRecord,
    OrganizationRecord,
    EventLedgerRecord,
    EventOutboxRecord,
    InstructionalContentKind,
    InstructionalWorkflowDecision,
    InstructionalWorkflowDecisionRequest,
    InstructionalWorkflowProjectionRecord,
    InstructionalWorkflowStageId,
    InstructionalWorkflowStageRecord,
    InstructionalWorkflowStageStatus,
    InstructionalWorkflowStatus,
    DeliveryDoraRow,
    DeliveryForecastPoint,
    DeliveryForecastSummary,
    DeliveryLifecycleRow,
    DeliveryTrendPoint,
    PerformanceOperationsSummary,
    PerformanceOperationsTrendPoint,
    PolicyRecord,
    PolicyRuleUpdateRequest,
    PortfolioRecord,
    PortfolioSummary,
    PromotionDetail,
    PromotionActionRequest,
    PromotionApprovalOverrideRequest,
    RequestDetail,
    RequestRelationship,
    ResumeAgentSessionRuntimeRequest,
    ReviewAssignmentOverrideRequest,
    ReviewDecisionRequest,
    ReviewQueueItem,
    RunCommandRequest,
    RuntimeRunCallbackRequest,
    RunStatus,
    RunDetail,
    RunRecord,
    StepStatus,
    TeamMemberRecord,
    TeamRecord,
    TenantRecord,
    UpdateIntegrationRequest,
    UpdateAgentSessionGovernanceRequest,
    UpdateOrganizationRequest,
    UpdateTenantRequest,
    UpdateTeamRequest,
    UpdateUserRequest,
    UserRecord,
    WorkflowTrendPoint,
    AddTeamMembershipRequest,
)
from app.models.request import AmendRequest, CancelRequest, CloneRequest, CreateRequestDraft, RequestCheckRun, RequestPriority, RequestRecord, RequestStatus, SubmitRequest, SupersedeRequest, TransitionRequest
from app.services.check_dispatch_service import check_dispatch_service
from app.services.collaboration_mode_service import collaboration_mode_service
from app.services.context_bundle_service import context_bundle_service
from app.services.deployment_service import deployment_service
from app.services.agent_provider_service import agent_provider_service
from app.services.event_store_service import event_store_service
from app.services.integration_security_service import integration_security_service
from app.services.local_account_service import local_account_service
from app.services.object_store_service import object_store_service
from app.services.policy_check_service import policy_check_service
from app.services.projection_service import projection_service
from app.services.request_state_bridge import get_request_state, record_request_event, update_request_state
from app.services.runtime_dispatch_service import runtime_dispatch_service
from app.domain.state_machine import (
    TRANSITION_RULES as _SM_TRANSITION_RULES,
    SUBMITTABLE_STATUSES as _SM_SUBMITTABLE_STATUSES,
    AMENDABLE_STATUSES as _SM_AMENDABLE_STATUSES,
    CANCELABLE_STATUSES as _SM_CANCELABLE_STATUSES,
    SLA_POLICY_RULES as _SM_SLA_POLICY_RULES,
    compute_sla_risk as _sm_compute_sla_risk,
    assert_valid_transition as _sm_assert_valid_transition,
)
from app.domain import template_engine as _te
from app.models.template import (
    CreateTemplateVersionRequest,
    TemplateRecord,
    TemplateStatus,
    TemplateStatusActionRequest,
    TemplateValidationIssue,
    TemplateValidationPreview,
    TemplateValidationPreviewField,
    TemplateValidationResult,
    UpdateTemplateDefinitionRequest,
)


class GovernanceRepository:
    _agent_stream_lock = threading.Lock()
    _agent_stream_inflight: set[str] = set()
    _instructional_template_stages = {
        "tmpl_assessment": [
            InstructionalWorkflowStageId.INSTRUCTIONAL_DESIGN_REVIEW,
            InstructionalWorkflowStageId.SME_REVIEW,
            InstructionalWorkflowStageId.ASSESSMENT_REVIEW,
            InstructionalWorkflowStageId.CERTIFICATION_COMPLIANCE_REVIEW,
        ],
        "tmpl_curriculum": [
            InstructionalWorkflowStageId.INSTRUCTIONAL_DESIGN_REVIEW,
            InstructionalWorkflowStageId.SME_REVIEW,
            InstructionalWorkflowStageId.CERTIFICATION_COMPLIANCE_REVIEW,
        ],
    }
    _instructional_stage_labels = {
        InstructionalWorkflowStageId.INSTRUCTIONAL_DESIGN_REVIEW: "Instructional Design Review",
        InstructionalWorkflowStageId.SME_REVIEW: "Subject Matter Expert Review",
        InstructionalWorkflowStageId.ASSESSMENT_REVIEW: "Assessment Review",
        InstructionalWorkflowStageId.CERTIFICATION_COMPLIANCE_REVIEW: "Certification Compliance Review",
    }

    # Delegated to app.domain.state_machine — kept as class attrs for backward compat
    SLA_POLICY_RULES = _SM_SLA_POLICY_RULES
    TRANSITION_RULES = _SM_TRANSITION_RULES
    SUBMITTABLE_STATUSES = _SM_SUBMITTABLE_STATUSES
    AMENDABLE_STATUSES = _SM_AMENDABLE_STATUSES
    CANCELABLE_STATUSES = _SM_CANCELABLE_STATUSES
    def __init__(self) -> None:
        # Seed data is now loaded via app.db.bootstrap.initialize_database()
        # called at API startup. No in-memory seed data is needed here.
        pass

    @staticmethod
    def _paginate(items: list, page: int, page_size: int) -> PaginatedResponse:
        start = (page - 1) * page_size
        end = start + page_size
        return PaginatedResponse.create(items=items[start:end], page=page, page_size=page_size, total_count=len(items))

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @classmethod
    def _is_instructional_template(cls, template_id: str) -> bool:
        return template_id in cls._instructional_template_stages

    @classmethod
    def _instructional_stage_ids(cls, template_id: str) -> list[InstructionalWorkflowStageId]:
        if not cls._is_instructional_template(template_id):
            raise ValueError(f"Template {template_id} is not an instructional governance template")
        return list(cls._instructional_template_stages[template_id])

    @staticmethod
    def _instructional_content_kind(template_id: str) -> InstructionalContentKind:
        return InstructionalContentKind.ASSESSMENT if template_id == "tmpl_assessment" else InstructionalContentKind.CURRICULUM_COURSE

    @staticmethod
    def _instructional_flightos_entry_id(row: RequestTable) -> str | None:
        value = (row.input_payload or {}).get("flightos_content_entry_id")
        return value if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _instructional_flightos_schema_id(row: RequestTable) -> str | None:
        value = (row.input_payload or {}).get("flightos_schema_id")
        if isinstance(value, str) and value.strip():
            return value
        return "assessment" if row.template_id == "tmpl_assessment" else "course"

    @staticmethod
    def _instructional_submitted_actor(audit_entries: list[AuditEntry]) -> str | None:
        for entry in audit_entries:
            if entry.action == "Submitted":
                return entry.actor
        return None

    @staticmethod
    def _instructional_timestamp_for_action(audit_entries: list[AuditEntry], action: str) -> str | None:
        for entry in reversed(audit_entries):
            if entry.action == action:
                return entry.timestamp
        return None

    @classmethod
    def _instructional_decisions_from_audit(
        cls,
        audit_entries: list[AuditEntry],
    ) -> dict[InstructionalWorkflowStageId, tuple[InstructionalWorkflowDecision, AuditEntry]]:
        decisions: dict[InstructionalWorkflowStageId, tuple[InstructionalWorkflowDecision, AuditEntry]] = {}
        for entry in audit_entries:
            if entry.action.startswith("Instructional Stage Approved: "):
                stage_name = entry.action.removeprefix("Instructional Stage Approved: ").strip()
                decisions[InstructionalWorkflowStageId(stage_name)] = (InstructionalWorkflowDecision.APPROVE, entry)
            elif entry.action.startswith("Instructional Stage Changes Requested: "):
                stage_name = entry.action.removeprefix("Instructional Stage Changes Requested: ").strip()
                decisions[InstructionalWorkflowStageId(stage_name)] = (InstructionalWorkflowDecision.REQUEST_CHANGES, entry)
        return decisions

    @staticmethod
    def _instructional_workflow_status(request_status: RequestStatus) -> InstructionalWorkflowStatus:
        if request_status == RequestStatus.DRAFT:
            return InstructionalWorkflowStatus.NOT_SUBMITTED
        if request_status in {RequestStatus.CHANGES_REQUESTED, RequestStatus.FAILED, RequestStatus.REJECTED, RequestStatus.VALIDATION_FAILED}:
            return InstructionalWorkflowStatus.CHANGES_REQUESTED
        if request_status in {RequestStatus.APPROVED, RequestStatus.PROMOTION_PENDING}:
            return InstructionalWorkflowStatus.APPROVED_FOR_RELEASE
        if request_status in {RequestStatus.PROMOTED, RequestStatus.COMPLETED, RequestStatus.ARCHIVED}:
            return InstructionalWorkflowStatus.RELEASED
        return InstructionalWorkflowStatus.IN_REVIEW

    @classmethod
    def _build_instructional_projection_from_row(
        cls,
        row: RequestTable,
        audit_entries: list[AuditEntry],
    ) -> InstructionalWorkflowProjectionRecord:
        stage_ids = cls._instructional_stage_ids(row.template_id)
        decisions = cls._instructional_decisions_from_audit(audit_entries)
        stages: list[InstructionalWorkflowStageRecord] = []
        blocking_stage: InstructionalWorkflowStageId | None = None
        approved_prefix = True

        for index, stage_id in enumerate(stage_ids, start=1):
            decision_entry = decisions.get(stage_id)
            status = InstructionalWorkflowStageStatus.PENDING
            decision = None
            decided_at = None
            decided_by_user_id = None
            notes = None
            if decision_entry:
                decision, entry = decision_entry
                decided_at = entry.timestamp
                decided_by_user_id = entry.actor
                notes = entry.reason_or_evidence
                if decision == InstructionalWorkflowDecision.APPROVE and approved_prefix:
                    status = InstructionalWorkflowStageStatus.APPROVED
                elif decision == InstructionalWorkflowDecision.REQUEST_CHANGES:
                    status = InstructionalWorkflowStageStatus.CHANGES_REQUESTED
                    approved_prefix = False
                    blocking_stage = stage_id
                else:
                    status = InstructionalWorkflowStageStatus.PENDING
                    approved_prefix = False
            elif approved_prefix:
                status = InstructionalWorkflowStageStatus.ACTIVE
                approved_prefix = False
                blocking_stage = stage_id
            stages.append(
                InstructionalWorkflowStageRecord(
                    stage_id=stage_id,
                    label=cls._instructional_stage_labels[stage_id],
                    status=status,
                    sequence=index,
                    decision=decision,
                    decided_at=decided_at,
                    decided_by_user_id=decided_by_user_id,
                    notes=notes,
                )
            )

        workflow_status = cls._instructional_workflow_status(RequestStatus(row.status))
        if workflow_status in {InstructionalWorkflowStatus.APPROVED_FOR_RELEASE, InstructionalWorkflowStatus.RELEASED}:
            stages = [
                stage.model_copy(update={"status": InstructionalWorkflowStageStatus.APPROVED})
                for stage in stages
            ]
            blocking_stage = stage_ids[-1] if stage_ids else None
        elif workflow_status == InstructionalWorkflowStatus.NOT_SUBMITTED:
            stages = [
                stage.model_copy(update={"status": InstructionalWorkflowStageStatus.PENDING, "decision": None, "decided_at": None, "decided_by_user_id": None, "notes": None})
                for stage in stages
            ]
            blocking_stage = None

        return InstructionalWorkflowProjectionRecord(
            request_id=row.id,
            tenant_id=row.tenant_id,
            flightos_content_entry_id=cls._instructional_flightos_entry_id(row) or row.id,
            flightos_schema_id=cls._instructional_flightos_schema_id(row),
            template_id=row.template_id,
            template_version=row.template_version,
            title=row.title,
            request_status=RequestStatus(row.status),
            workflow_status=workflow_status,
            content_kind=cls._instructional_content_kind(row.template_id),
            current_stage_id=blocking_stage,
            submitted_at=cls._instructional_timestamp_for_action(audit_entries, "Submitted"),
            submitted_by_user_id=cls._instructional_submitted_actor(audit_entries),
            approved_for_release_at=cls._instructional_timestamp_for_action(audit_entries, "Transitioned to approved"),
            released_at=cls._instructional_timestamp_for_action(audit_entries, "Transitioned to promoted")
            or cls._instructional_timestamp_for_action(audit_entries, "Transitioned to completed"),
            stages=stages,
        )

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
        with SessionLocal() as session:
            records = self._list_canonical_request_records(session, tenant_id=tenant_id)
            workflow_request_ids = None
            if workflow:
                workflow_request_ids = {
                    row.request_id
                    for row in session.scalars(
                        select(RunTable).where((RunTable.workflow == workflow) | (RunTable.workflow_identity == workflow))
                    ).all()
                }
        if status:
            records = [record for record in records if record.status == status]
        if owner_team_id:
            records = [record for record in records if record.owner_team_id == owner_team_id]
        if request_id:
            records = [record for record in records if record.id == request_id]
        if workflow:
            records = [
                record
                for record in records
                if record.workflow_binding_id == workflow or record.template_id == workflow or (workflow_request_ids and record.id in workflow_request_ids)
            ]
        if federation == "with_projection":
            records = [record for record in records if record.federated_projection_count > 0]
        elif federation == "with_conflict":
            records = [record for record in records if record.federated_conflict_count > 0]
        return self._paginate(records, page, page_size)

    def get_request(self, request_id: str, tenant_id: str | None = None) -> RequestDetail:
        with SessionLocal() as session:
            request_row = session.get(RequestTable, request_id)
            if request_row is None:
                from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

                return DynamoDbGovernancePersistenceAdapter().get_request(request_id, tenant_id)
            self._ensure_request_tenant_access(request_row, tenant_id)
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
        if request_row is None:
            raise StopIteration(request_id)
        request = self._request_from_row(request_row)
        latest_run = self._run_detail_from_row(run_row) if run_row else None
        artifact_ids = [row.id for row in artifact_rows]
        include_review_blockers = request.status in {
            RequestStatus.AWAITING_REVIEW.value,
            RequestStatus.UNDER_REVIEW.value,
            RequestStatus.CHANGES_REQUESTED.value,
        }
        blockers = [row.blocking_status for row in review_rows if row.blocking_status] if include_review_blockers else []
        blockers.extend([f"{check.name}: {check.detail}" for check in check_rows if check.state != "passed"])
        blockers.extend(
            [f"Checks {run.status}: {run.trigger_reason}" for run in check_run_rows if run.scope == "request" and run.status in {"queued", "running"}]
        )
        if request.status == RequestStatus.CHANGES_REQUESTED.value:
            blockers.append("Reviewer requested changes before progress can continue.")
        if request.status == RequestStatus.PROMOTION_PENDING.value and promotion_row is not None:
            blockers.append(promotion_row.execution_readiness)
        elif request.status == RequestStatus.PROMOTION_PENDING.value:
            blockers.append("Promotion authorization still pending.")
        messages_by_session: dict[str, list[AgentSessionMessageTable]] = {}
        for message in agent_messages:
            messages_by_session.setdefault(message.session_id, []).append(message)
        session_records = [
            self._agent_session_from_row(row, integration_rows.get(row.integration_id), messages_by_session.get(row.id, []))
            for row in agent_session_rows
        ]
        active_agent_waits = [row for row in session_records if row.awaiting_human and row.status in {"active", "waiting_on_human"}]
        if active_agent_waits:
            blockers.append(f"Agent session waiting for human input: {active_agent_waits[0].agent_label}")
        next_required_action = self._next_action_for_request(request.status, latest_run is not None, promotion_row is not None)
        return RequestDetail(
            request=request,
            latest_run_id=latest_run.id if latest_run else None,
            latest_artifact_ids=artifact_ids,
            active_blockers=blockers,
            check_results=[
                CheckResult.model_validate(
                    {
                        "id": check.id,
                        "request_id": check.request_id,
                        "promotion_id": check.promotion_id,
                        "name": check.name,
                        "state": check.state,
                        "detail": check.detail,
                        "severity": check.severity,
                        "evidence": check.evidence,
                        "evaluated_at": check.evaluated_at.isoformat().replace("+00:00", "Z"),
                        "evaluated_by": check.evaluated_by,
                    }
                )
                for check in check_rows
            ],
            check_runs=[self._check_run_from_row(row) for row in check_run_rows],
            agent_sessions=session_records,
            next_required_action=next_required_action,
            predecessors=[self._relationship_from_predecessor_row(row) for row in predecessor_rows],
            successors=[self._relationship_from_successor_row(row) for row in successor_rows],
        )

    def list_instructional_workflow_projections(
        self,
        page: int,
        page_size: int,
        tenant_id: str | None = None,
        flightos_content_entry_id: str | None = None,
        template_id: str | None = None,
        workflow_status: str | None = None,
    ) -> PaginatedResponse[InstructionalWorkflowProjectionRecord]:
        with SessionLocal() as session:
            stmt = select(RequestTable).order_by(desc(RequestTable.updated_at))
            if tenant_id:
                stmt = stmt.where(RequestTable.tenant_id == tenant_id)
            rows = [row for row in session.scalars(stmt).all() if self._is_instructional_template(row.template_id)]
        projections = [
            self._build_instructional_projection_from_row(row, self.list_audit_entries(row.id, row.tenant_id))
            for row in rows
            if self._instructional_flightos_entry_id(row)
        ]
        if flightos_content_entry_id:
            projections = [projection for projection in projections if projection.flightos_content_entry_id == flightos_content_entry_id]
        if template_id:
            projections = [projection for projection in projections if projection.template_id == template_id]
        if workflow_status:
            projections = [projection for projection in projections if projection.workflow_status.value == workflow_status]
        return self._paginate(projections, page, page_size)

    def get_instructional_workflow_projection(self, request_id: str, tenant_id: str | None = None) -> InstructionalWorkflowProjectionRecord:
        with SessionLocal() as session:
            row = session.get(RequestTable, request_id)
            if row is None:
                raise StopIteration(request_id)
            self._ensure_request_tenant_access(row, tenant_id)
            if not self._is_instructional_template(row.template_id):
                raise ValueError(f"Request {request_id} is not an instructional governance request")
        return self._build_instructional_projection_from_row(row, self.list_audit_entries(request_id, row.tenant_id))

    def list_templates(self, tenant_id: str | None = None, include_non_published: bool = False) -> list[TemplateRecord]:
        with SessionLocal() as session:
            stmt = select(TemplateTable)
            if tenant_id:
                stmt = stmt.where(TemplateTable.tenant_id == tenant_id)
            if not include_non_published:
                stmt = stmt.where(TemplateTable.status == TemplateStatus.PUBLISHED.value)
            rows = session.scalars(stmt.order_by(TemplateTable.id, TemplateTable.version)).all()
        return [self._template_from_row(row) for row in rows]

    def create_template_version(self, payload: CreateTemplateVersionRequest, actor_id: str, tenant_id: str) -> TemplateRecord:
        with SessionLocal() as session:
            template_id = payload.template_id.strip()
            version = payload.version.strip()
            if not template_id:
                raise ValueError("Template id is required")
            if not version:
                raise ValueError("Template version is required")
            existing_row = session.scalars(
                select(TemplateTable).where(
                    TemplateTable.tenant_id == tenant_id,
                    TemplateTable.id == template_id,
                    TemplateTable.version == version,
                )
            ).first()
            if existing_row is not None:
                raise ValueError(f"Template version {template_id}@{version} already exists")
            source_row = None
            if payload.source_version:
                source_row = session.scalars(
                    select(TemplateTable).where(
                        TemplateTable.tenant_id == tenant_id,
                        TemplateTable.id == template_id,
                        TemplateTable.version == payload.source_version,
                    )
                ).first()
                if source_row is None:
                    raise StopIteration(f"{template_id}@{payload.source_version}")
            elif template_id in {row.id for row in session.scalars(select(TemplateTable).where(TemplateTable.tenant_id == tenant_id)).all()}:
                source_row = session.scalars(
                    select(TemplateTable)
                    .where(TemplateTable.tenant_id == tenant_id, TemplateTable.id == template_id)
                    .order_by(desc(TemplateTable.created_at))
                ).first()
            now = datetime.now(timezone.utc)
            row = TemplateTable(
                tenant_id=tenant_id,
                id=template_id,
                version=version,
                name=payload.name or (source_row.name if source_row else template_id.replace("tmpl_", "").replace("_", " ").title()),
                description=payload.description or (source_row.description if source_row else f"Draft template for {template_id}."),
                status=TemplateStatus.DRAFT.value,
                template_schema=deepcopy(source_row.template_schema) if source_row else {"required": [], "properties": {}, "routing": {}},
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.flush()
            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="template.version_created",
                aggregate_type="template",
                aggregate_id=f"{row.id}@{row.version}",
                actor=actor_id,
                detail=f"Created draft template version {row.id}@{row.version}",
                payload={"template_id": row.id, "template_version": row.version, "source_version": payload.source_version},
            )
            session.commit()
            session.refresh(row)
        return self._template_from_row(row)

    def update_template_definition(
        self,
        template_id: str,
        version: str,
        payload: UpdateTemplateDefinitionRequest,
        actor_id: str,
        tenant_id: str,
    ) -> TemplateRecord:
        with SessionLocal() as session:
            row = session.scalars(
                select(TemplateTable).where(
                    TemplateTable.tenant_id == tenant_id,
                    TemplateTable.id == template_id,
                    TemplateTable.version == version,
                )
            ).first()
            if row is None:
                raise StopIteration(f"{template_id}@{version}")
            if row.status != TemplateStatus.DRAFT.value:
                raise ValueError("Only draft template versions can be edited")
            validation = self._validate_template_definition(payload.template_schema)
            errors = [issue for issue in validation.issues if issue.level == "error"]
            if errors:
                raise ValueError("; ".join(f"{issue.path}: {issue.message}" for issue in errors))
            row.name = payload.name
            row.description = payload.description
            row.template_schema = payload.template_schema
            row.updated_at = datetime.now(timezone.utc)
            session.flush()
            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="template.definition_updated",
                aggregate_type="template",
                aggregate_id=f"{row.id}@{row.version}",
                actor=actor_id,
                detail=f"Updated template definition for {row.id}@{row.version}",
                payload={"template_id": row.id, "template_version": row.version},
            )
            session.commit()
            session.refresh(row)
        return self._template_from_row(row)

    def validate_template_definition(self, template_id: str, version: str, tenant_id: str) -> TemplateValidationResult:
        with SessionLocal() as session:
            row = session.scalars(
                select(TemplateTable).where(
                    TemplateTable.tenant_id == tenant_id,
                    TemplateTable.id == template_id,
                    TemplateTable.version == version,
                )
            ).first()
        if row is None:
            raise StopIteration(f"{template_id}@{version}")
        return self._validate_template_definition(row.template_schema or {})

    def delete_template_version(self, template_id: str, version: str, actor_id: str, tenant_id: str) -> None:
        with SessionLocal() as session:
            row = session.scalars(
                select(TemplateTable).where(
                    TemplateTable.tenant_id == tenant_id,
                    TemplateTable.id == template_id,
                    TemplateTable.version == version,
                )
            ).first()
            if row is None:
                raise StopIteration(f"{template_id}@{version}")
            if row.status != TemplateStatus.DRAFT.value:
                raise ValueError("Only draft template versions can be deleted")
            session.delete(row)
            session.flush()
            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="template.version_deleted",
                aggregate_type="template",
                aggregate_id=f"{template_id}@{version}",
                actor=actor_id,
                detail=f"Deleted draft template version {template_id}@{version}",
                payload={"template_id": template_id, "template_version": version},
            )
            session.commit()

    def update_template_status(
        self,
        template_id: str,
        version: str,
        target_status: TemplateStatus,
        actor_id: str,
        tenant_id: str,
        note: str | None = None,
    ) -> TemplateRecord:
        with SessionLocal() as session:
            row = session.scalars(
                select(TemplateTable).where(
                    TemplateTable.tenant_id == tenant_id,
                    TemplateTable.id == template_id,
                    TemplateTable.version == version,
                )
            ).first()
            if row is None:
                raise StopIteration(f"{template_id}@{version}")
            if target_status == TemplateStatus.PUBLISHED:
                published_rows = session.scalars(
                    select(TemplateTable).where(
                        TemplateTable.tenant_id == tenant_id,
                        TemplateTable.id == template_id,
                        TemplateTable.status == TemplateStatus.PUBLISHED.value,
                        TemplateTable.version != version,
                    )
                ).all()
                for published_row in published_rows:
                    published_row.status = TemplateStatus.DEPRECATED.value
                    published_row.updated_at = datetime.now(timezone.utc)
            row.status = target_status.value
            row.updated_at = datetime.now(timezone.utc)
            session.flush()
            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type=f"template.{target_status.value}",
                aggregate_type="template",
                aggregate_id=f"{row.id}@{row.version}",
                actor=actor_id,
                detail=f"Marked template {row.id}@{row.version} as {target_status.value}",
                payload={"template_id": row.id, "template_version": row.version, "note": note or ""},
            )
            session.commit()
            session.refresh(row)
        return self._template_from_row(row)

    def list_runs(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
        workflow: str | None = None,
        owner: str | None = None,
        request_id: str | None = None,
        federation: str | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[RunRecord]:
        with SessionLocal() as session:
            rows = session.scalars(select(RunTable).order_by(desc(RunTable.updated_at))).all()
            request_tenant_map = {
                row.id: row.tenant_id
                for row in session.scalars(select(RequestTable).where(RequestTable.id.in_([item.request_id for item in rows]))).all()
            } if rows else {}
            for run_row in rows:
                if run_row.request_id not in request_tenant_map:
                    request = get_request_state(run_row.request_id, None)
                    if request is not None:
                        request_tenant_map[run_row.request_id] = request.tenant_id
            projection_rows = session.scalars(
                select(ProjectionMappingTable).where(
                    ProjectionMappingTable.entity_type == "request",
                    ProjectionMappingTable.entity_id.in_([item.request_id for item in rows]) if rows else False,
                )
            ).all() if rows else []
        projections_by_request: dict[str, list[ProjectionMappingTable]] = {}
        for projection in projection_rows:
            projections_by_request.setdefault(projection.entity_id, []).append(projection)
        run_details = [self._run_detail_from_row(row, projection_rows=projections_by_request.get(row.request_id, [])) for row in rows]
        pairs = [(RunRecord.model_validate(detail.model_dump()), detail) for detail in run_details]
        if tenant_id:
            pairs = [(row, detail) for row, detail in pairs if request_tenant_map.get(row.request_id) == tenant_id]
        if status:
            pairs = [(row, detail) for row, detail in pairs if row.status == status]
        if workflow:
            pairs = [(row, detail) for row, detail in pairs if row.workflow == workflow or detail.workflow_identity == workflow]
        if owner:
            pairs = [
                (row, detail)
                for row, detail in pairs
                if row.owner_team == owner or any(step.owner == owner for step in detail.steps)
            ]
        if request_id:
            pairs = [(row, detail) for row, detail in pairs if row.request_id == request_id]
        if federation == "with_projection":
            pairs = [(row, detail) for row, detail in pairs if row.federated_projection_count > 0]
        elif federation == "with_conflict":
            pairs = [(row, detail) for row, detail in pairs if row.federated_conflict_count > 0]
        return self._paginate([row for row, _detail in pairs], page, page_size)

    def get_run(self, run_id: str, tenant_id: str | None = None) -> RunDetail:
        with SessionLocal() as session:
            row = session.get(RunTable, run_id)
            request = None
            if row is not None:
                request = self._get_request_record(session, row.request_id, tenant_id)
            dispatch_rows = session.scalars(select(RuntimeDispatchTable).where(RuntimeDispatchTable.run_id == run_id).order_by(desc(RuntimeDispatchTable.dispatched_at))).all()
            signal_rows = session.scalars(select(RuntimeSignalTable).where(RuntimeSignalTable.run_id == run_id).order_by(desc(RuntimeSignalTable.received_at))).all()
            projection_rows = (
                session.scalars(
                    select(ProjectionMappingTable)
                    .where(
                        ProjectionMappingTable.entity_type == "request",
                        ProjectionMappingTable.entity_id == request.id,
                        ProjectionMappingTable.tenant_id == request.tenant_id,
                    )
                    .order_by(desc(ProjectionMappingTable.last_synced_at), desc(ProjectionMappingTable.last_projected_at))
                ).all()
                if request is not None
                else []
            )
        if row is None:
            raise StopIteration(run_id)
        return self._run_detail_from_row(row, dispatch_rows, signal_rows, projection_rows)

    def command_run(self, run_id: str, payload: RunCommandRequest, tenant_id: str | None = None) -> RunDetail:
        with SessionLocal() as session:
            run_row = session.get(RunTable, run_id)
            if run_row is None:
                raise StopIteration(run_id)
            request = self._get_request_record(session, run_row.request_id, tenant_id)
            request_row = session.get(RequestTable, run_row.request_id)
            command = payload.command
            if command not in {"Pause", "Resume", "Retry Step", "Cancel Run"}:
                raise ValueError(f"Unsupported run command {command}")
            self._dispatch_run_to_runtime(session, request, run_id, command.lower().replace(" ", "_"), payload.actor_id, force=True)
            now = datetime.now(timezone.utc)
            if command == "Pause":
                run_row.status = RunStatus.PAUSED.value
                run_row.waiting_reason = "Paused by operator command"
                run_row.current_step_output_summary = "Runtime accepted pause command."
            elif command == "Resume":
                run_row.status = RunStatus.RUNNING.value
                run_row.waiting_reason = None
                run_row.current_step_output_summary = "Runtime accepted resume command."
            elif command == "Retry Step":
                run_row.status = RunStatus.RUNNING.value
                run_row.waiting_reason = None
                run_row.current_step_output_summary = "Runtime accepted retry command."
                run_row.progress_percent = max(run_row.progress_percent - 5, 10)
            elif command == "Cancel Run":
                run_row.status = RunStatus.FAILED.value
                run_row.waiting_reason = "Canceled by operator command"
                run_row.failure_reason = "Run canceled through governance control plane"
                run_row.current_step_output_summary = "Runtime accepted cancel command."
                if request_row is not None:
                    request_row.status = RequestStatus.FAILED.value
                    request_row.updated_at = now
                    request_row.updated_by = payload.actor_id
                    request_row.version += 1
                    self._append_event(
                        session=session,
                        request_id=request_row.id,
                        actor=payload.actor_id,
                        action="Run Canceled",
                        reason_or_evidence=payload.reason,
                    )
                else:
                    update_request_state(run_row.request_id, request.tenant_id, payload.actor_id, status=RequestStatus.FAILED)
                    record_request_event(run_row.request_id, request.tenant_id, payload.actor_id, "Run Canceled", payload.reason)
            run_row.updated_at = now
            dispatch_rows = session.scalars(select(RuntimeDispatchTable).where(RuntimeDispatchTable.run_id == run_id).order_by(desc(RuntimeDispatchTable.dispatched_at))).all()
            signal_rows = session.scalars(select(RuntimeSignalTable).where(RuntimeSignalTable.run_id == run_id).order_by(desc(RuntimeSignalTable.received_at))).all()
            projection_rows = session.scalars(
                select(ProjectionMappingTable)
                .where(
                    ProjectionMappingTable.entity_type == "request",
                    ProjectionMappingTable.entity_id == request.id,
                    ProjectionMappingTable.tenant_id == request.tenant_id,
                )
                .order_by(desc(ProjectionMappingTable.last_synced_at), desc(ProjectionMappingTable.last_projected_at))
            ).all()
            session.commit()
            session.refresh(run_row)
            return self._run_detail_from_row(run_row, dispatch_rows, signal_rows, projection_rows)

    def reconcile_run(self, run_id: str, payload: RuntimeRunCallbackRequest) -> RunDetail:
        with SessionLocal() as session:
            run_row = session.get(RunTable, run_id)
            if run_row is None:
                raise StopIteration(run_id)
            request = self._get_request_record(session, run_row.request_id, None)
            request_row = session.get(RequestTable, run_row.request_id)
            existing_signal = session.scalars(
                select(RuntimeSignalTable).where(
                    RuntimeSignalTable.run_id == run_id,
                    RuntimeSignalTable.event_id == payload.event_id,
                )
            ).first()
            if existing_signal is not None:
                dispatch_rows = session.scalars(select(RuntimeDispatchTable).where(RuntimeDispatchTable.run_id == run_id).order_by(desc(RuntimeDispatchTable.dispatched_at))).all()
                signal_rows = session.scalars(select(RuntimeSignalTable).where(RuntimeSignalTable.run_id == run_id).order_by(desc(RuntimeSignalTable.received_at))).all()
                projection_rows = session.scalars(
                    select(ProjectionMappingTable)
                    .where(
                        ProjectionMappingTable.entity_type == "request",
                        ProjectionMappingTable.entity_id == request.id,
                        ProjectionMappingTable.tenant_id == request.tenant_id,
                    )
                    .order_by(desc(ProjectionMappingTable.last_synced_at), desc(ProjectionMappingTable.last_projected_at))
                ).all()
                return self._run_detail_from_row(run_row, dispatch_rows, signal_rows, projection_rows)
            now = datetime.now(timezone.utc)
            session.add(
                RuntimeSignalTable(
                    tenant_id=request.tenant_id,
                    run_id=run_id,
                    request_id=request.id,
                    event_id=payload.event_id,
                    source=payload.source,
                    status=payload.status,
                    current_step=payload.current_step,
                    detail=payload.detail,
                    payload={
                        **payload.payload,
                        "progress_percent": payload.progress_percent,
                        "waiting_reason": payload.waiting_reason,
                        "failure_reason": payload.failure_reason,
                    },
                    received_at=now,
                )
            )
            event_store_service.append(
                session,
                tenant_id=request.tenant_id,
                event_type=f"runtime.signal.{payload.status}",
                aggregate_type="run",
                aggregate_id=run_id,
                request_id=request.id,
                run_id=run_id,
                actor=payload.source,
                detail=payload.detail,
                payload=payload.model_dump(mode="python"),
            )
            run_row.status = payload.status
            if payload.current_step:
                run_row.current_step = payload.current_step
            if payload.progress_percent is not None:
                run_row.progress_percent = payload.progress_percent
            run_row.waiting_reason = payload.waiting_reason
            run_row.failure_reason = payload.failure_reason
            run_row.current_step_output_summary = payload.detail
            run_row.updated_at = now

            if payload.status == RunStatus.COMPLETED.value:
                if request_row is not None:
                    request_row.status = RequestStatus.COMPLETED.value
                    request_row.updated_at = now
                    request_row.updated_by = payload.source
                    request_row.version += 1
                    self._append_event(session, request_row.id, payload.source, "Runtime Completed", payload.detail)
                else:
                    update_request_state(run_row.request_id, request.tenant_id, payload.source, status=RequestStatus.COMPLETED)
                    record_request_event(run_row.request_id, request.tenant_id, payload.source, "Runtime Completed", payload.detail)
                self._update_artifact_review_state(session, request.id, artifact_status="completed", review_state="approved", stale_review=False, promotion_relevant=True)
            elif payload.status == RunStatus.FAILED.value:
                if request_row is not None:
                    request_row.status = RequestStatus.FAILED.value
                    request_row.updated_at = now
                    request_row.updated_by = payload.source
                    request_row.version += 1
                    self._append_event(session, request_row.id, payload.source, "Runtime Failed", payload.detail)
                else:
                    update_request_state(run_row.request_id, request.tenant_id, payload.source, status=RequestStatus.FAILED)
                    record_request_event(run_row.request_id, request.tenant_id, payload.source, "Runtime Failed", payload.detail)
                self._update_artifact_review_state(session, request.id, artifact_status="failed", review_state="pending", stale_review=False, promotion_relevant=True)
            elif payload.status == RunStatus.RUNNING.value and request.status == RequestStatus.QUEUED.value:
                if request_row is not None:
                    request_row.status = RequestStatus.IN_EXECUTION.value
                    request_row.updated_at = now
                    request_row.updated_by = payload.source
                    request_row.version += 1
                else:
                    update_request_state(run_row.request_id, request.tenant_id, payload.source, status=RequestStatus.IN_EXECUTION)

            session.flush()
            dispatch_rows = session.scalars(select(RuntimeDispatchTable).where(RuntimeDispatchTable.run_id == run_id).order_by(desc(RuntimeDispatchTable.dispatched_at))).all()
            signal_rows = session.scalars(select(RuntimeSignalTable).where(RuntimeSignalTable.run_id == run_id).order_by(desc(RuntimeSignalTable.received_at))).all()
            projection_rows = session.scalars(
                select(ProjectionMappingTable)
                .where(
                    ProjectionMappingTable.entity_type == "request",
                    ProjectionMappingTable.entity_id == request.id,
                    ProjectionMappingTable.tenant_id == request.tenant_id,
                )
                .order_by(desc(ProjectionMappingTable.last_synced_at), desc(ProjectionMappingTable.last_projected_at))
            ).all()
            session.commit()
            session.refresh(run_row)
            return self._run_detail_from_row(run_row, dispatch_rows, signal_rows, projection_rows)

    def list_artifacts(self, page: int, page_size: int, tenant_id: str | None = None) -> PaginatedResponse[ArtifactRecord]:
        with SessionLocal() as session:
            rows = session.scalars(select(ArtifactTable).order_by(desc(ArtifactTable.updated_at))).all()
            request_tenant_map = {
                row.id: row.tenant_id
                for row in session.scalars(select(RequestTable).where(RequestTable.id.in_([item.request_id for item in rows]))).all()
            } if rows else {}
            for artifact_row in rows:
                if artifact_row.request_id not in request_tenant_map:
                    request = get_request_state(artifact_row.request_id, None)
                    if request is not None:
                        request_tenant_map[artifact_row.request_id] = request.tenant_id
        artifact_rows = [self._artifact_record_from_row(row) for row in rows]
        if tenant_id:
            artifact_rows = [row for row in artifact_rows if request_tenant_map.get(row.request_id) == tenant_id]
        return self._paginate(artifact_rows, page, page_size)

    def get_artifact(self, artifact_id: str, tenant_id: str | None = None) -> ArtifactDetail:
        with SessionLocal() as session:
            row = session.get(ArtifactTable, artifact_id)
            if row is not None:
                self._get_request_record(session, row.request_id, tenant_id)
            event_rows = session.scalars(select(ArtifactEventTable).where(ArtifactEventTable.artifact_id == artifact_id).order_by(ArtifactEventTable.timestamp)).all()
            lineage_rows = session.scalars(select(ArtifactLineageEdgeTable).where(ArtifactLineageEdgeTable.artifact_id == artifact_id).order_by(ArtifactLineageEdgeTable.created_at)).all()
        if row is None:
            raise StopIteration(artifact_id)
        return self._artifact_detail_from_row(row, event_rows, lineage_rows)

    def list_review_queue(
        self,
        page: int,
        page_size: int,
        assigned_reviewer: str | None = None,
        blocking_only: bool = False,
        stale_only: bool = False,
        request_id: str | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[ReviewQueueItem]:
        with SessionLocal() as session:
            rows = session.scalars(select(ReviewQueueTable).order_by(desc(ReviewQueueTable.priority), ReviewQueueTable.id)).all()
            sql_request_rows = {
                row.id: row
                for row in session.scalars(select(RequestTable).where(RequestTable.id.in_([item.request_id for item in rows]))).all()
            } if rows else {}
        request_rows: dict[str, RequestTable | RequestRecord] = dict(sql_request_rows)
        if tenant_id:
            for queue_row in rows:
                if queue_row.request_id in request_rows:
                    continue
                request_state = get_request_state(queue_row.request_id, tenant_id)
                if request_state is not None:
                    request_rows[queue_row.request_id] = request_state
        queue_rows = [self._review_queue_item_from_row(row, request_rows.get(row.request_id)) for row in rows]
        if tenant_id:
            queue_rows = [
                row
                for row in queue_rows
                if request_rows.get(row.request_id) is not None and request_rows[row.request_id].tenant_id == tenant_id
            ]
        if assigned_reviewer:
            queue_rows = [row for row in queue_rows if row.assigned_reviewer == assigned_reviewer]
        if blocking_only:
            queue_rows = [row for row in queue_rows if row.blocking_status not in {"Approved", "Clear"}]
        if stale_only:
            queue_rows = [row for row in queue_rows if row.stale]
        if request_id:
            queue_rows = [row for row in queue_rows if row.request_id == request_id]
        return self._paginate(queue_rows, page, page_size)

    def get_promotion(self, promotion_id: str, tenant_id: str | None = None) -> PromotionDetail:
        with SessionLocal() as session:
            row = session.get(PromotionTable, promotion_id)
            if row is not None:
                request_row = session.get(RequestTable, row.request_id)
                if request_row is not None:
                    self._ensure_request_tenant_access(request_row, tenant_id)
                elif tenant_id is not None and get_request_state(row.request_id, tenant_id) is None:
                    raise StopIteration(row.request_id)
            check_rows = session.scalars(select(CheckResultTable).where(CheckResultTable.promotion_id == promotion_id).order_by(CheckResultTable.name)).all()
            override_rows = session.scalars(select(CheckOverrideTable).where(CheckOverrideTable.promotion_id == promotion_id).order_by(CheckOverrideTable.created_at)).all()
            check_run_rows = session.scalars(select(CheckRunTable).where(CheckRunTable.promotion_id == promotion_id).order_by(desc(CheckRunTable.queued_at))).all()
            deployment_rows = session.scalars(
                select(DeploymentExecutionTable).where(DeploymentExecutionTable.promotion_id == promotion_id).order_by(desc(DeploymentExecutionTable.executed_at))
            ).all()
        if row is None:
            raise StopIteration(promotion_id)
        return self._promotion_detail_from_row(row, check_rows, override_rows, check_run_rows, deployment_rows)

    def record_review_decision(self, review_id: str, payload: ReviewDecisionRequest, tenant_id: str | None = None) -> ReviewQueueItem:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        request = None
        with SessionLocal() as session:
            review_row = session.get(ReviewQueueTable, review_id)
            if review_row is None:
                raise StopIteration(review_id)
            request = get_request_state(review_row.request_id, tenant_id)
            if request is None:
                raise StopIteration(review_row.request_id)
            request_row = session.get(RequestTable, review_row.request_id)
            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
            decision = payload.decision
            now = datetime.now(timezone.utc)
            if decision == "approve":
                review_row.blocking_status = "Approved"
                review_row.stale = False
                self._update_artifact_review_state(session, review_row.request_id, artifact_status="approved", review_state="approved", stale_review=False)
                if request_row is not None:
                    request_row.status = RequestStatus.APPROVED.value
                current_run_id = request_row.current_run_id if request_row is not None else request.current_run_id
                if current_run_id:
                    run_row = session.get(RunTable, current_run_id)
                    if run_row is not None:
                        run_row.status = RunStatus.COMPLETED.value
                        run_row.current_step = "Review Approved"
                        run_row.progress_percent = 100
                        run_row.waiting_reason = None
                        run_row.updated_at = now
            elif decision == "changes_requested":
                review_row.blocking_status = "Changes requested"
                review_row.stale = True
                self._update_artifact_review_state(session, review_row.request_id, artifact_status="changes_requested", review_state="changes_requested", stale_review=True)
                if request_row is not None:
                    request_row.status = RequestStatus.CHANGES_REQUESTED.value
            else:
                raise ValueError(f"Unsupported review decision {decision}")
            if request_row is not None:
                request_row.updated_at = now
                request_row.updated_by = payload.actor_id
                request_row.version += 1
                self._append_event(
                    session=session,
                    request_id=request_row.id,
                    actor=payload.actor_id,
                    action=f"Review {decision.replace('_', ' ').title()}",
                    reason_or_evidence=payload.reason,
                )
            session.commit()
            session.refresh(review_row)
            if request_row is None:
                target_status = RequestStatus.APPROVED if decision == "approve" else RequestStatus.CHANGES_REQUESTED
                update_request_state(
                    review_row.request_id,
                    request.tenant_id,
                    payload.actor_id,
                    status=target_status,
                    updated_at=now,
                    updated_by=payload.actor_id,
                )
                record_request_event(
                    review_row.request_id,
                    request.tenant_id,
                    payload.actor_id,
                    f"Review {decision.replace('_', ' ').title()}",
                    payload.reason,
                    status=target_status.value,
                )
                return self._review_queue_item_from_row(review_row, get_request_state(review_row.request_id, request.tenant_id))
            session.refresh(request_row)
            return self._review_queue_item_from_row(review_row, request_row)

    def override_review_assignment(self, review_id: str, payload: ReviewAssignmentOverrideRequest, tenant_id: str | None = None) -> ReviewQueueItem:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        request = None
        with SessionLocal() as session:
            review_row = session.get(ReviewQueueTable, review_id)
            if review_row is None:
                raise StopIteration(review_id)
            request = get_request_state(review_row.request_id, tenant_id)
            if request is None:
                raise StopIteration(review_row.request_id)
            request_row = session.get(RequestTable, review_row.request_id)
            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
            previous_reviewer = review_row.assigned_reviewer
            review_row.assigned_reviewer = payload.assigned_reviewer
            review_row.blocking_status = f"Reassigned to {payload.assigned_reviewer}"
            now = datetime.now(timezone.utc)
            if request_row is not None:
                self._append_event(
                    session=session,
                    request_id=request_row.id,
                    actor=payload.actor_id,
                    action="Review Assignment Overridden",
                    reason_or_evidence=f"{payload.reason}. {previous_reviewer} -> {payload.assigned_reviewer}",
                )
            event_store_service.append(
                session,
                tenant_id=request.tenant_id,
                event_type="review.assignment_overridden",
                aggregate_type="review",
                aggregate_id=review_row.id,
                request_id=review_row.request_id,
                actor=payload.actor_id,
                detail=payload.reason,
                payload={
                    "review_id": review_row.id,
                    "from_reviewer": previous_reviewer,
                    "to_reviewer": payload.assigned_reviewer,
                },
            )
            if request_row is not None:
                request_row.updated_at = now
                request_row.updated_by = payload.actor_id
                request_row.version += 1
            session.commit()
            session.refresh(review_row)
            if request_row is None:
                update_request_state(
                    review_row.request_id,
                    request.tenant_id,
                    payload.actor_id,
                    updated_at=now,
                    updated_by=payload.actor_id,
                )
                record_request_event(
                    review_row.request_id,
                    request.tenant_id,
                    payload.actor_id,
                    "Review Assignment Overridden",
                    f"{payload.reason}. {previous_reviewer} -> {payload.assigned_reviewer}",
                )
                return self._review_queue_item_from_row(review_row, get_request_state(review_row.request_id, request.tenant_id))
            return self._review_queue_item_from_row(review_row, request_row)

    def apply_promotion_action(self, promotion_id: str, payload: PromotionActionRequest, tenant_id: str | None = None) -> PromotionDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        request = None
        with SessionLocal() as session:
            promotion_row = session.get(PromotionTable, promotion_id)
            if promotion_row is None:
                raise StopIteration(promotion_id)
            request = get_request_state(promotion_row.request_id, tenant_id)
            if request is None:
                raise StopIteration(promotion_row.request_id)
            request_row = session.get(RequestTable, promotion_row.request_id)
            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
            check_rows = session.scalars(select(CheckResultTable).where(CheckResultTable.promotion_id == promotion_id)).all()
            override_rows = session.scalars(select(CheckOverrideTable).where(CheckOverrideTable.promotion_id == promotion_id)).all()
            action = payload.action
            now = datetime.now(timezone.utc)
            history = list(promotion_row.promotion_history)
            if action == "dry_run":
                promotion_row.execution_readiness = policy_check_service.promotion_readiness(check_rows, override_rows, promotion_row.required_approvals)
                history.append({"timestamp": now.isoformat().replace("+00:00", "Z"), "actor": payload.actor_id, "action": "Dry run executed"})
                event_store_service.append(
                    session,
                    tenant_id=request.tenant_id,
                    event_type="promotion.dry_run",
                    aggregate_type="promotion",
                    aggregate_id=promotion_row.id,
                    request_id=promotion_row.request_id,
                    promotion_id=promotion_row.id,
                    actor=payload.actor_id,
                    detail=payload.reason,
                    payload={"readiness": promotion_row.execution_readiness},
                )
            elif action == "authorize":
                approvals = [dict(approval) for approval in promotion_row.required_approvals]
                for approval in approvals:
                    if approval["state"] == "pending":
                        approval["state"] = "approved"
                promotion_row.required_approvals = approvals
                promotion_row.execution_readiness = policy_check_service.promotion_readiness(check_rows, override_rows, approvals)
                history.append({"timestamp": now.isoformat().replace("+00:00", "Z"), "actor": payload.actor_id, "action": "Promotion authorized"})
                event_store_service.append(
                    session,
                    tenant_id=request.tenant_id,
                    event_type="promotion.authorized",
                    aggregate_type="promotion",
                    aggregate_id=promotion_row.id,
                    request_id=promotion_row.request_id,
                    promotion_id=promotion_row.id,
                    actor=payload.actor_id,
                    detail=payload.reason,
                    payload={"approvals": approvals},
                )
            elif action == "execute":
                if check_dispatch_service.has_pending_promotion_check_run(session, promotion_id):
                    raise ValueError("Promotion checks are still queued or running")
                if not policy_check_service.promotion_ready(check_rows, override_rows, promotion_row.required_approvals):
                    raise ValueError("Promotion cannot execute until required checks pass or are overridden and approvals are approved")
                integration_row = session.scalars(
                    select(IntegrationTable).where(
                        IntegrationTable.tenant_id == request.tenant_id,
                        IntegrationTable.type == "runtime",
                        IntegrationTable.status == "connected",
                    )
                ).first()
                if integration_row is None:
                    raise ValueError("No connected runtime integration is available for this tenant")
                deployment_payload = {
                    "promotion_id": promotion_row.id,
                    "request_id": promotion_row.request_id,
                    "target": promotion_row.target,
                    "strategy": promotion_row.strategy,
                    "artifact_ids": [row.id for row in session.scalars(select(ArtifactTable).where(ArtifactTable.request_id == promotion_row.request_id)).all()],
                }
                deployment_response = deployment_service.execute(integration_row, deployment_payload)
                deployment_row = DeploymentExecutionTable(
                    id=self._next_deployment_execution_id(session),
                    tenant_id=request.tenant_id,
                    promotion_id=promotion_row.id,
                    request_id=promotion_row.request_id,
                    integration_id=integration_row.id,
                    target=promotion_row.target,
                    strategy=promotion_row.strategy,
                    status=str(deployment_response.get("status", "deployed")),
                    external_reference=str(deployment_response.get("deployment_id")) if deployment_response.get("deployment_id") else None,
                    detail=str(deployment_response.get("summary", "Deployment executed successfully.")),
                    payload=deployment_payload,
                    response_payload=deployment_response,
                    executed_at=now,
                )
                session.add(deployment_row)
                event_store_service.append(
                    session,
                    tenant_id=request.tenant_id,
                    event_type="promotion.executed",
                    aggregate_type="promotion",
                    aggregate_id=promotion_row.id,
                    request_id=promotion_row.request_id,
                    promotion_id=promotion_row.id,
                    actor=payload.actor_id,
                    detail=str(deployment_response.get("summary", "Deployment executed successfully.")),
                    payload={
                        "target": promotion_row.target,
                        "strategy": promotion_row.strategy,
                        "deployment_execution_id": deployment_row.id,
                        "external_reference": deployment_row.external_reference,
                    },
                )
                approvals = [dict(approval) for approval in promotion_row.required_approvals]
                for approval in approvals:
                    approval["state"] = "approved"
                promotion_row.required_approvals = approvals
                promotion_row.execution_readiness = f"Promotion executed successfully via {integration_row.name}."
                if request_row is not None:
                    request_row.status = RequestStatus.PROMOTED.value
                    request_row.updated_at = now
                    request_row.updated_by = payload.actor_id
                    request_row.version += 1
                self._update_artifact_review_state(session, promotion_row.request_id, artifact_status="promoted", review_state="approved", stale_review=False, promotion_relevant=True)
                history.append(
                    {
                        "timestamp": now.isoformat().replace("+00:00", "Z"),
                        "actor": payload.actor_id,
                        "action": f"Promotion executed via {integration_row.name} ({deployment_row.external_reference or deployment_row.id})",
                    }
                )
                if request_row is not None:
                    self._append_event(
                        session=session,
                        request_id=request_row.id,
                        actor=payload.actor_id,
                        action="Promotion Executed",
                        reason_or_evidence=f"{payload.reason}; external_reference={deployment_row.external_reference or deployment_row.id}",
                    )
            else:
                raise ValueError(f"Unsupported promotion action {action}")
            promotion_row.promotion_history = history
            session.commit()
            if request_row is None and action == "execute":
                update_request_state(
                    promotion_row.request_id,
                    request.tenant_id,
                    payload.actor_id,
                    status=RequestStatus.PROMOTED,
                    updated_at=now,
                    updated_by=payload.actor_id,
                )
                record_request_event(
                    promotion_row.request_id,
                    request.tenant_id,
                    payload.actor_id,
                    "Promotion Executed",
                    f"{payload.reason}; external_reference={deployment_row.external_reference or deployment_row.id}",
                    status=RequestStatus.PROMOTED.value,
                )
            session.refresh(promotion_row)
            refreshed_checks = session.scalars(select(CheckResultTable).where(CheckResultTable.promotion_id == promotion_id).order_by(CheckResultTable.name)).all()
            refreshed_overrides = session.scalars(select(CheckOverrideTable).where(CheckOverrideTable.promotion_id == promotion_id).order_by(CheckOverrideTable.created_at)).all()
            refreshed_runs = session.scalars(select(CheckRunTable).where(CheckRunTable.promotion_id == promotion_id).order_by(desc(CheckRunTable.queued_at))).all()
            refreshed_deployments = session.scalars(
                select(DeploymentExecutionTable).where(DeploymentExecutionTable.promotion_id == promotion_id).order_by(desc(DeploymentExecutionTable.executed_at))
            ).all()
            return self._promotion_detail_from_row(promotion_row, refreshed_checks, refreshed_overrides, refreshed_runs, refreshed_deployments)

    def evaluate_check(self, promotion_id: str, check_id: str, payload: CheckEvaluationRequest, tenant_id: str | None = None) -> PromotionDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        with SessionLocal() as session:
            promotion_row = session.get(PromotionTable, promotion_id)
            if promotion_row is None:
                raise StopIteration(promotion_id)
            request = get_request_state(promotion_row.request_id, tenant_id)
            if request is None:
                raise StopIteration(promotion_row.request_id)
            request_row = session.get(RequestTable, promotion_row.request_id)
            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
            check_row = session.get(CheckResultTable, check_id)
            if check_row is None or check_row.promotion_id != promotion_id:
                raise StopIteration(check_id)
            check_row.state = payload.state
            check_row.detail = payload.detail
            check_row.evidence = payload.evidence
            check_row.evaluated_at = datetime.now(timezone.utc)
            check_row.evaluated_by = payload.actor_id
            policy_check_service.sync_promotion_checks(session, promotion_row)
            promotion_row.execution_readiness = self._promotion_readiness_from_db(session, promotion_row)
            history = list(promotion_row.promotion_history)
            history.append({"timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "actor": payload.actor_id, "action": f"Check evaluated: {check_row.name}"})
            promotion_row.promotion_history = history
            session.commit()
            session.refresh(promotion_row)
            return self._promotion_detail_from_row(
                promotion_row,
                session.scalars(select(CheckResultTable).where(CheckResultTable.promotion_id == promotion_id).order_by(CheckResultTable.name)).all(),
                session.scalars(select(CheckOverrideTable).where(CheckOverrideTable.promotion_id == promotion_id).order_by(CheckOverrideTable.created_at)).all(),
                session.scalars(select(CheckRunTable).where(CheckRunTable.promotion_id == promotion_id).order_by(desc(CheckRunTable.queued_at))).all(),
                session.scalars(select(DeploymentExecutionTable).where(DeploymentExecutionTable.promotion_id == promotion_id).order_by(desc(DeploymentExecutionTable.executed_at))).all(),
            )

    def override_check(self, promotion_id: str, check_id: str, payload: CheckOverrideRequest, tenant_id: str | None = None) -> PromotionDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        with SessionLocal() as session:
            promotion_row = session.get(PromotionTable, promotion_id)
            if promotion_row is None:
                raise StopIteration(promotion_id)
            request = get_request_state(promotion_row.request_id, tenant_id)
            if request is None:
                raise StopIteration(promotion_row.request_id)
            request_row = session.get(RequestTable, promotion_row.request_id)
            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
            check_row = session.get(CheckResultTable, check_id)
            if check_row is None or check_row.promotion_id != promotion_id:
                raise StopIteration(check_id)
            override_id = self._next_check_override_id(session)
            now = datetime.now(timezone.utc)
            session.add(
                CheckOverrideTable(
                    id=override_id,
                    check_result_id=check_row.id,
                    request_id=promotion_row.request_id,
                    promotion_id=promotion_id,
                    state="approved",
                    reason=payload.reason,
                    requested_by=payload.actor_id,
                    decided_by=payload.actor_id,
                    created_at=now,
                    decided_at=now,
                )
            )
            policy_check_service.sync_promotion_checks(session, promotion_row)
            promotion_row.execution_readiness = self._promotion_readiness_from_db(session, promotion_row)
            history = list(promotion_row.promotion_history)
            history.append({"timestamp": now.isoformat().replace("+00:00", "Z"), "actor": payload.actor_id, "action": f"Override approved: {check_row.name}"})
            promotion_row.promotion_history = history
            session.commit()
            session.refresh(promotion_row)
            return self._promotion_detail_from_row(
                promotion_row,
                session.scalars(select(CheckResultTable).where(CheckResultTable.promotion_id == promotion_id).order_by(CheckResultTable.name)).all(),
                session.scalars(select(CheckOverrideTable).where(CheckOverrideTable.promotion_id == promotion_id).order_by(CheckOverrideTable.created_at)).all(),
                session.scalars(select(CheckRunTable).where(CheckRunTable.promotion_id == promotion_id).order_by(desc(CheckRunTable.queued_at))).all(),
                session.scalars(select(DeploymentExecutionTable).where(DeploymentExecutionTable.promotion_id == promotion_id).order_by(desc(DeploymentExecutionTable.executed_at))).all(),
            )

    def run_promotion_checks(self, promotion_id: str, payload: CheckRunRequest, tenant_id: str | None = None) -> PromotionDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        with SessionLocal() as session:
            promotion_row = session.get(PromotionTable, promotion_id)
            if promotion_row is None:
                raise StopIteration(promotion_id)
            request = get_request_state(promotion_row.request_id, tenant_id)
            if request is None:
                raise StopIteration(promotion_row.request_id)
            request_row = session.get(RequestTable, promotion_row.request_id)
            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
            check_dispatch_service.enqueue_promotion_checks(session, promotion_id, promotion_row.request_id, payload.actor_id, payload.reason)
            history = list(promotion_row.promotion_history)
            history.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "actor": payload.actor_id,
                    "action": "Promotion checks queued",
                }
            )
            promotion_row.promotion_history = history
            session.commit()
            session.refresh(promotion_row)
            return self._promotion_detail_from_row(
                promotion_row,
                session.scalars(select(CheckResultTable).where(CheckResultTable.promotion_id == promotion_id).order_by(CheckResultTable.name)).all(),
                session.scalars(select(CheckOverrideTable).where(CheckOverrideTable.promotion_id == promotion_id).order_by(CheckOverrideTable.created_at)).all(),
                session.scalars(select(CheckRunTable).where(CheckRunTable.promotion_id == promotion_id).order_by(desc(CheckRunTable.queued_at))).all(),
                session.scalars(select(DeploymentExecutionTable).where(DeploymentExecutionTable.promotion_id == promotion_id).order_by(desc(DeploymentExecutionTable.executed_at))).all(),
            )

    def override_promotion_approval(self, promotion_id: str, payload: PromotionApprovalOverrideRequest, tenant_id: str | None = None) -> PromotionDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        with SessionLocal() as session:
            promotion_row = session.get(PromotionTable, promotion_id)
            if promotion_row is None:
                raise StopIteration(promotion_id)
            request = get_request_state(promotion_row.request_id, tenant_id)
            if request is None:
                raise StopIteration(promotion_row.request_id)
            request_row = session.get(RequestTable, promotion_row.request_id)
            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
            approvals = [dict(approval) for approval in promotion_row.required_approvals]
            target_approval = next((approval for approval in approvals if approval.get("reviewer") == payload.reviewer), None)
            if target_approval is None:
                raise ValueError(f"Promotion approval reviewer {payload.reviewer} not found")
            target_approval["reviewer"] = payload.replacement_reviewer
            target_approval["state"] = "pending"
            promotion_row.required_approvals = approvals
            promotion_row.execution_readiness = self._promotion_readiness_from_db(session, promotion_row)
            history = list(promotion_row.promotion_history)
            history.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "actor": payload.actor_id,
                    "action": f"Approval reassigned: {payload.reviewer} -> {payload.replacement_reviewer}",
                }
            )
            promotion_row.promotion_history = history
            if request_row is not None:
                self._append_event(
                    session=session,
                    request_id=request_row.id,
                    actor=payload.actor_id,
                    action="Promotion Approval Overridden",
                    reason_or_evidence=f"{payload.reason}. {payload.reviewer} -> {payload.replacement_reviewer}",
                )
            event_store_service.append(
                session,
                tenant_id=request.tenant_id,
                event_type="promotion.approval_overridden",
                aggregate_type="promotion",
                aggregate_id=promotion_row.id,
                request_id=promotion_row.request_id,
                promotion_id=promotion_row.id,
                actor=payload.actor_id,
                detail=payload.reason,
                payload={
                    "from_reviewer": payload.reviewer,
                    "to_reviewer": payload.replacement_reviewer,
                    "approvals": approvals,
                },
            )
            session.commit()
            if request_row is None:
                record_request_event(
                    promotion_row.request_id,
                    request.tenant_id,
                    payload.actor_id,
                    "Promotion Approval Overridden",
                    f"{payload.reason}. {payload.reviewer} -> {payload.replacement_reviewer}",
                )
            session.refresh(promotion_row)
            return self._promotion_detail_from_row(
                promotion_row,
                session.scalars(select(CheckResultTable).where(CheckResultTable.promotion_id == promotion_id).order_by(CheckResultTable.name)).all(),
                session.scalars(select(CheckOverrideTable).where(CheckOverrideTable.promotion_id == promotion_id).order_by(CheckOverrideTable.created_at)).all(),
                session.scalars(select(CheckRunTable).where(CheckRunTable.promotion_id == promotion_id).order_by(desc(CheckRunTable.queued_at))).all(),
                session.scalars(select(DeploymentExecutionTable).where(DeploymentExecutionTable.promotion_id == promotion_id).order_by(desc(DeploymentExecutionTable.executed_at))).all(),
            )

    def run_request_checks(self, request_id: str, payload: RequestCheckRun, tenant_id: str | None = None) -> RequestRecord:
        with SessionLocal() as session:
            request = self._get_request_record(session, request_id, tenant_id)
            row = session.get(RequestTable, request_id)
            check_dispatch_service.enqueue_request_checks(session, request_id, payload.actor_id, payload.reason)
            session.commit()
            if row is not None:
                session.refresh(row)
                return self._request_from_row(row)
        refreshed = get_request_state(request_id, request.tenant_id)
        return refreshed or request

    def _promotion_detail_from_row(
        self,
        row: PromotionTable,
        check_rows: list[CheckResultTable],
        override_rows: list[CheckOverrideTable],
        check_run_rows: list[CheckRunTable] | None = None,
        deployment_rows: list[DeploymentExecutionTable] | None = None,
    ) -> PromotionDetail:
        return PromotionDetail.model_validate(
            {
                "id": row.id,
                "request_id": row.request_id,
                "target": row.target,
                "strategy": row.strategy,
                "required_checks": row.required_checks,
                "check_results": [
                    {
                        "id": check.id,
                        "request_id": check.request_id,
                        "promotion_id": check.promotion_id,
                        "name": check.name,
                        "state": check.state,
                        "detail": check.detail,
                        "severity": check.severity,
                        "evidence": check.evidence,
                        "evaluated_at": check.evaluated_at.isoformat().replace("+00:00", "Z"),
                        "evaluated_by": check.evaluated_by,
                    }
                    for check in check_rows
                ],
                "check_runs": [self._check_run_from_row(check_run) for check_run in (check_run_rows or [])],
                "overrides": [
                    {
                        "id": override.id,
                        "check_result_id": override.check_result_id,
                        "request_id": override.request_id,
                        "promotion_id": override.promotion_id,
                        "state": override.state,
                        "reason": override.reason,
                        "requested_by": override.requested_by,
                        "decided_by": override.decided_by,
                        "created_at": override.created_at.isoformat().replace("+00:00", "Z"),
                        "decided_at": override.decided_at.isoformat().replace("+00:00", "Z"),
                    }
                    for override in override_rows
                ],
                "required_approvals": row.required_approvals,
                "stale_warnings": row.stale_warnings,
                "execution_readiness": row.execution_readiness,
                "deployment_executions": [
                    {
                        "id": deployment.id,
                        "promotion_id": deployment.promotion_id,
                        "request_id": deployment.request_id,
                        "integration_id": deployment.integration_id,
                        "target": deployment.target,
                        "strategy": deployment.strategy,
                        "status": deployment.status,
                        "external_reference": deployment.external_reference,
                        "detail": deployment.detail,
                        "payload": deployment.payload,
                        "response_payload": deployment.response_payload,
                        "executed_at": deployment.executed_at.isoformat().replace("+00:00", "Z"),
                    }
                    for deployment in (deployment_rows or [])
                ],
                "promotion_history": row.promotion_history,
            }
        )

    def list_capabilities(self, page: int, page_size: int, tenant_id: str | None = None) -> PaginatedResponse[CapabilityRecord]:
        with SessionLocal() as session:
            stmt = select(CapabilityTable)
            if tenant_id:
                stmt = stmt.where(CapabilityTable.tenant_id == tenant_id)
            rows = session.scalars(stmt.order_by(desc(CapabilityTable.updated_at))).all()
        capability_rows = [self._capability_record_from_row(row) for row in rows]
        return self._paginate(capability_rows, page, page_size)

    def get_capability(self, capability_id: str, tenant_id: str | None = None) -> CapabilityDetail:
        with SessionLocal() as session:
            row = session.get(CapabilityTable, capability_id)
            if row is not None and tenant_id and row.tenant_id != tenant_id:
                raise PermissionError(capability_id)
        if row is None:
            raise StopIteration(capability_id)
        return self._capability_detail_from_row(row)

    def list_workflow_analytics(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
    ) -> list[AnalyticsWorkflowRow]:
        with SessionLocal() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            request_rows = self._list_canonical_request_records(session, tenant_id=tenant_id, cutoff=cutoff)
            scope_rows = session.scalars(select(PortfolioScopeTable).where(PortfolioScopeTable.tenant_id == tenant_id)).all() if tenant_id else []
            request_rows = self._filter_request_rows_for_analytics(request_rows, tenant_id, team_id, user_id, portfolio_id, scope_rows)
            request_ids = {row.id for row in request_rows}
            run_rows = [row for row in session.scalars(select(RunTable).where(RunTable.updated_at >= cutoff)).all() if row.request_id in request_ids]
            review_rows = [row for row in session.scalars(select(ReviewQueueTable)).all() if row.request_id in request_ids]
            projection_rows = [
                row
                for row in session.scalars(select(ProjectionMappingTable).where(ProjectionMappingTable.entity_type == "request")).all()
                if row.entity_id in request_ids
            ]

        grouped: dict[str, dict[str, object]] = {}
        for request_row in request_rows:
            workflow = request_row.workflow_binding_id or request_row.template_id
            duration = self._as_utc(request_row.updated_at) - self._as_utc(request_row.created_at)
            bucket = grouped.setdefault(
                workflow,
                {
                    "durations": [],
                    "total": 0,
                    "failed": 0,
                    "review_count": 0,
                    "review_stale": 0,
                    "cost_points": 0.0,
                    "projection_count": 0,
                    "requests_with_projection": set(),
                    "conflict_count": 0,
                },
            )
            bucket["durations"].append(duration)
            bucket["total"] += 1
            if request_row.status in {RequestStatus.FAILED.value, RequestStatus.REJECTED.value, RequestStatus.CANCELED.value}:
                bucket["failed"] += 1
            bucket["cost_points"] += 1.5 if request_row.priority == "high" else 2.25 if request_row.priority == "urgent" else 1.0

        run_by_request = {run.request_id: run for run in run_rows}
        for review_row in review_rows:
            request_run = run_by_request.get(review_row.request_id)
            workflow = request_run.workflow_identity if request_run else "unbound_review"
            bucket = grouped.setdefault(
                workflow,
                {
                    "durations": [],
                    "total": 0,
                    "failed": 0,
                    "review_count": 0,
                    "review_stale": 0,
                    "cost_points": 0.0,
                    "projection_count": 0,
                    "requests_with_projection": set(),
                    "conflict_count": 0,
                },
            )
            bucket["review_count"] += 1
            if review_row.stale:
                bucket["review_stale"] += 1

        request_workflow = {row.id: row.workflow_binding_id or row.template_id for row in request_rows}
        for projection_row in projection_rows:
            workflow = request_workflow.get(projection_row.entity_id)
            if not workflow:
                continue
            bucket = grouped.setdefault(
                workflow,
                {
                    "durations": [],
                    "total": 0,
                    "failed": 0,
                    "review_count": 0,
                    "review_stale": 0,
                    "cost_points": 0.0,
                    "projection_count": 0,
                    "requests_with_projection": set(),
                    "conflict_count": 0,
                },
            )
            bucket["projection_count"] += 1
            bucket["requests_with_projection"].add(projection_row.entity_id)
            if projection_service.detect_conflicts(projection_row.id, projection_row.tenant_id):
                bucket["conflict_count"] += 1

        rows: list[AnalyticsWorkflowRow] = []
        for workflow, bucket in grouped.items():
            durations = sorted(bucket["durations"])
            total = max(int(bucket["total"]), 1)
            p95_index = min(len(durations) - 1, max(0, int(len(durations) * 0.95) - 1)) if durations else 0
            requests_with_projection = len(bucket["requests_with_projection"])
            rows.append(
                AnalyticsWorkflowRow(
                    workflow=workflow,
                    avg_cycle_time=self._format_timedelta(sum(durations, timedelta()) / len(durations)) if durations else "0m",
                    p95_duration=self._format_timedelta(durations[p95_index]) if durations else "0m",
                    failure_rate=self._format_percent(int(bucket["failed"]), total),
                    review_delay=f"{int(bucket['review_count'])} queued / {int(bucket['review_stale'])} stale",
                    cost_per_execution=f"${bucket['cost_points'] / total:.2f}",
                    trend="Stable" if int(bucket["failed"]) == 0 else "Needs attention",
                    federated_projection_count=int(bucket["projection_count"]),
                    federated_conflict_count=int(bucket["conflict_count"]),
                    federated_coverage=self._format_percent(requests_with_projection, total),
                )
            )
        return sorted(rows, key=lambda row: row.workflow)

    def list_workflow_trends(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
        workflow: str | None = None,
    ) -> list[WorkflowTrendPoint]:
        with SessionLocal() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            request_rows = self._list_canonical_request_records(session, tenant_id=tenant_id, cutoff=cutoff)
            scope_rows = session.scalars(select(PortfolioScopeTable).where(PortfolioScopeTable.tenant_id == tenant_id)).all() if tenant_id else []
            request_rows = self._filter_request_rows_for_analytics(request_rows, tenant_id, team_id, user_id, portfolio_id, scope_rows)
            if workflow:
                request_rows = [row for row in request_rows if (row.workflow_binding_id or row.template_id) == workflow]
            request_ids = {row.id for row in request_rows}
            review_rows = [row for row in session.scalars(select(ReviewQueueTable)).all() if row.request_id in request_ids and row.stale]

        review_stale_by_request: dict[str, int] = {}
        for row in review_rows:
            review_stale_by_request[row.request_id] = review_stale_by_request.get(row.request_id, 0) + 1

        grouped: dict[str, dict[str, float]] = {}
        for request_row in request_rows:
            period_start = self._as_utc(request_row.updated_at).date().isoformat()
            bucket = grouped.setdefault(
                period_start,
                {"request_count": 0.0, "failed_count": 0.0, "cycle_hours": 0.0, "review_stale_count": 0.0, "cost_points": 0.0},
            )
            bucket["request_count"] += 1
            bucket["failed_count"] += 1 if request_row.status in {RequestStatus.FAILED.value, RequestStatus.REJECTED.value, RequestStatus.CANCELED.value} else 0
            bucket["cycle_hours"] += max((self._as_utc(request_row.updated_at) - self._as_utc(request_row.created_at)).total_seconds() / 3600, 0.0)
            bucket["review_stale_count"] += review_stale_by_request.get(request_row.id, 0)
            bucket["cost_points"] += 1.5 if request_row.priority == "high" else 2.25 if request_row.priority == "urgent" else 1.0

        rows: list[WorkflowTrendPoint] = []
        for period_start in sorted(grouped.keys()):
            bucket = grouped[period_start]
            request_count = max(int(bucket["request_count"]), 1)
            rows.append(
                WorkflowTrendPoint(
                    period_start=period_start,
                    request_count=int(bucket["request_count"]),
                    failed_count=int(bucket["failed_count"]),
                    avg_cycle_time_hours=round(bucket["cycle_hours"] / request_count, 2),
                    review_stale_count=int(bucket["review_stale_count"]),
                    cost_per_execution=round(bucket["cost_points"] / request_count, 2),
                )
            )
        return rows

    def list_agent_analytics(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
    ) -> list[AnalyticsAgentRow]:
        with SessionLocal() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            request_rows = self._list_canonical_request_records(session, tenant_id=tenant_id)
            scope_rows = session.scalars(select(PortfolioScopeTable).where(PortfolioScopeTable.tenant_id == tenant_id)).all() if tenant_id else []
            request_rows = self._filter_request_rows_for_analytics(request_rows, tenant_id, team_id, user_id, portfolio_id, scope_rows)
            request_ids = {row.id for row in request_rows}
            run_rows = [row for row in session.scalars(select(RunTable).where(RunTable.updated_at >= cutoff)).all() if row.request_id in request_ids]

        grouped: dict[str, dict[str, float]] = {}
        for run_row in run_rows:
            owners = {step.get("owner") for step in run_row.steps if step.get("owner", "").startswith("agent")}
            for owner in owners:
                bucket = grouped.setdefault(owner, {"invocations": 0, "success": 0, "retry": 0, "duration": 0.0, "quality": 0.0})
                bucket["invocations"] += 1
                bucket["success"] += 1 if run_row.status == RunStatus.COMPLETED.value else 0
                bucket["retry"] += 1 if "Retry Step" in run_row.command_surface else 0
                bucket["duration"] += max(run_row.progress_percent, 1)
                bucket["quality"] += 95.0 if run_row.status == RunStatus.COMPLETED.value else 80.0 if run_row.status in {RunStatus.RUNNING.value, RunStatus.WAITING.value} else 60.0

        rows: list[AnalyticsAgentRow] = []
        for agent, bucket in grouped.items():
            invocations = max(int(bucket["invocations"]), 1)
            avg_minutes = bucket["duration"] / invocations / 10
            rows.append(
                AnalyticsAgentRow(
                    agent=agent,
                    invocations=invocations,
                    success_rate=self._format_percent(int(bucket["success"]), invocations),
                    retry_rate=self._format_percent(int(bucket["retry"]), invocations),
                    avg_duration=f"{avg_minutes:.1f}m",
                    cost_per_invocation=f"${1.25 + (avg_minutes * 0.35):.2f}",
                    quality_score=f"{bucket['quality'] / invocations:.1f}",
                )
            )
        return sorted(rows, key=lambda row: row.agent)

    def list_agent_trends(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
        agent: str | None = None,
    ) -> list[AgentTrendPoint]:
        with SessionLocal() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            request_rows = self._list_canonical_request_records(session, tenant_id=tenant_id)
            scope_rows = session.scalars(select(PortfolioScopeTable).where(PortfolioScopeTable.tenant_id == tenant_id)).all() if tenant_id else []
            request_rows = self._filter_request_rows_for_analytics(request_rows, tenant_id, team_id, user_id, portfolio_id, scope_rows)
            request_ids = {row.id for row in request_rows}
            run_rows = [row for row in session.scalars(select(RunTable).where(RunTable.updated_at >= cutoff)).all() if row.request_id in request_ids]

        grouped: dict[str, dict[str, float]] = {}
        for run_row in run_rows:
            owners = sorted({step.get("owner") for step in run_row.steps if step.get("owner", "").startswith("agent")})
            for owner in owners:
                if agent and owner != agent:
                    continue
                period_start = self._as_utc(run_row.updated_at).date().isoformat()
                bucket = grouped.setdefault(
                    period_start,
                    {"invocations": 0.0, "success": 0.0, "retry": 0.0, "duration_minutes": 0.0, "quality": 0.0},
                )
                bucket["invocations"] += 1
                bucket["success"] += 1 if run_row.status == RunStatus.COMPLETED.value else 0
                bucket["retry"] += 1 if "Retry Step" in run_row.command_surface else 0
                bucket["duration_minutes"] += (max(run_row.progress_percent, 1) / 10)
                bucket["quality"] += 95.0 if run_row.status == RunStatus.COMPLETED.value else 80.0 if run_row.status in {RunStatus.RUNNING.value, RunStatus.WAITING.value} else 60.0

        rows: list[AgentTrendPoint] = []
        for period_start in sorted(grouped.keys()):
            bucket = grouped[period_start]
            invocations = max(int(bucket["invocations"]), 1)
            rows.append(
                AgentTrendPoint(
                    period_start=period_start,
                    invocation_count=int(bucket["invocations"]),
                    success_rate=round((bucket["success"] / invocations) * 100, 2),
                    retry_rate=round((bucket["retry"] / invocations) * 100, 2),
                    avg_duration_minutes=round(bucket["duration_minutes"] / invocations, 2),
                    quality_score=round(bucket["quality"] / invocations, 2),
                )
            )
        return rows

    def list_bottleneck_analytics(self, days: int = 30, tenant_id: str | None = None) -> list[AnalyticsBottleneckRow]:
        with SessionLocal() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            request_rows = self._list_canonical_request_records(session, tenant_id=tenant_id)
            request_ids = {row.id for row in request_rows if tenant_id is None or row.tenant_id == tenant_id}
            review_rows = [row for row in session.scalars(select(ReviewQueueTable)).all() if row.request_id in request_ids]
            run_rows = [row for row in session.scalars(select(RunTable).where(RunTable.updated_at >= cutoff)).all() if row.request_id in request_ids]

        rows: list[AnalyticsBottleneckRow] = []
        for review_row in review_rows:
            rows.append(
                AnalyticsBottleneckRow(
                    workflow="Review Queue",
                    step=review_row.artifact_or_changeset,
                    avg_wait_time="4h" if "Due in 4h" in review_row.sla else "2h" if "Due in 2h" in review_row.sla else review_row.sla,
                    block_count=1 if review_row.blocking_status in {"Blocking request progress", "Changes requested"} else 0,
                    reviewer_delay=review_row.assigned_reviewer,
                    trend="Stale" if review_row.stale else "Stable",
                )
            )
        for run_row in run_rows:
            if run_row.waiting_reason:
                rows.append(
                    AnalyticsBottleneckRow(
                        workflow=run_row.workflow_identity,
                        step=run_row.current_step,
                        avg_wait_time=run_row.elapsed_time,
                        block_count=1 if run_row.status in {RunStatus.WAITING.value, RunStatus.FAILED.value} else 0,
                        reviewer_delay=run_row.waiting_reason,
                        trend="Blocked" if run_row.status == RunStatus.WAITING.value else "Recovering",
                    )
                )
        return rows

    def list_audit_entries(self, request_id: str, tenant_id: str | None = None) -> list[AuditEntry]:
        request = get_request_state(request_id, tenant_id) if tenant_id is not None else None
        if tenant_id is not None and request is None:
            raise StopIteration(request_id)
        if request is not None:
            tenant_id = request.tenant_id
        with SessionLocal() as session:
            if request is None:
                request_row = self._get_request_row(session, request_id)
                self._ensure_request_tenant_access(request_row, tenant_id)
                tenant_id = request_row.tenant_id
            rows = session.scalars(select(RequestEventTable).where(RequestEventTable.request_id == request_id).order_by(RequestEventTable.timestamp)).all()
            projection_rows = session.scalars(
                select(ProjectionMappingTable).where(
                    ProjectionMappingTable.entity_type == "request",
                    ProjectionMappingTable.entity_id == request_id,
                    ProjectionMappingTable.tenant_id == tenant_id,
                )
            ).all()
            projection_logs: list[tuple[ProjectionMappingTable, ReconciliationLogTable]] = []
            if projection_rows:
                projection_ids = [row.id for row in projection_rows]
                log_rows = session.scalars(
                    select(ReconciliationLogTable)
                    .where(ReconciliationLogTable.projection_id.in_(projection_ids))
                    .order_by(ReconciliationLogTable.created_at)
                ).all()
                projection_by_id = {row.id: row for row in projection_rows}
                projection_logs = [
                    (projection_by_id[log_row.projection_id], log_row)
                    for log_row in log_rows
                    if log_row.projection_id in projection_by_id
                ]
        if request is None:
            entries = [
                AuditEntry(
                    timestamp=row.timestamp.isoformat().replace("+00:00", "Z"),
                    actor=row.actor,
                    action=row.action,
                    object_type=row.object_type,
                    object_id=row.object_id,
                    reason_or_evidence=row.reason_or_evidence,
                    event_class="canonical",
                    source_system="RGP",
                    related_entity_type="request",
                    related_entity_id=request_id,
                    lineage=[f"request:{request_id}", f"{row.object_type}:{row.object_id}"],
                )
                for row in rows
            ]
        else:
            from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

            dynamo_entries = DynamoDbGovernancePersistenceAdapter().list_audit_entries(request_id, tenant_id=request.tenant_id)
            sql_entries = [
                AuditEntry(
                    timestamp=row.timestamp.isoformat().replace("+00:00", "Z"),
                    actor=row.actor,
                    action=row.action,
                    object_type=row.object_type,
                    object_id=row.object_id,
                    reason_or_evidence=row.reason_or_evidence,
                    event_class="canonical",
                    source_system="RGP",
                    related_entity_type="request",
                    related_entity_id=request_id,
                    lineage=[f"request:{request_id}", f"{row.object_type}:{row.object_id}"],
                )
                for row in rows
            ]
            entries = dynamo_entries if dynamo_entries else sql_entries
        entries.extend(
            AuditEntry(
                timestamp=log_row.created_at.isoformat().replace("+00:00", "Z"),
                actor=log_row.resolved_by or "system",
                action=self._audit_action_label(log_row.action, projection_row),
                object_type="projection",
                object_id=projection_row.id,
                reason_or_evidence=log_row.detail or f"{projection_row.external_system} {log_row.action}",
                event_class=self._audit_event_class(log_row.action),
                source_system=projection_row.external_system,
                integration_id=projection_row.integration_id,
                projection_id=projection_row.id,
                related_entity_type=projection_row.entity_type,
                related_entity_id=projection_row.entity_id,
                lineage=[
                    f"{projection_row.entity_type}:{projection_row.entity_id}",
                    f"projection:{projection_row.id}",
                    f"external:{projection_row.external_system}",
                    *([f"external_ref:{projection_row.external_ref}"] if projection_row.external_ref else []),
                ],
            )
            for projection_row, log_row in projection_logs
        )
        return sorted(entries, key=lambda entry: entry.timestamp)

    def list_run_audit_entries(self, run_id: str, tenant_id: str | None = None) -> list[AuditEntry]:
        with SessionLocal() as session:
            run_row = session.get(RunTable, run_id)
            if run_row is None:
                raise StopIteration(run_id)
            request = self._get_request_record(session, run_row.request_id, tenant_id)
        entries = self.list_audit_entries(run_row.request_id, request.tenant_id)
        entries.append(
            AuditEntry(
                timestamp=run_row.updated_at.isoformat().replace("+00:00", "Z"),
                actor="system",
                action="Run Status Snapshot",
                object_type="run",
                object_id=run_id,
                reason_or_evidence=f"status={run_row.status} workflow={run_row.workflow_identity}",
                event_class="canonical",
                source_system="RGP",
                related_entity_type="request",
                related_entity_id=run_row.request_id,
                lineage=[f"workflow:{run_row.workflow_identity}", f"request:{run_row.request_id}", f"run:{run_id}"],
            )
        )
        return sorted(entries, key=lambda entry: entry.timestamp)

    def list_workflow_audit_entries(self, workflow: str, tenant_id: str | None = None, limit: int = 200) -> list[AuditEntry]:
        with SessionLocal() as session:
            request_records = [
                row
                for row in self._list_canonical_request_records(session, tenant_id=tenant_id)
                if row.workflow_binding_id == workflow or row.template_id == workflow
            ]
            request_ids = {row.id for row in request_records}
            run_rows = session.scalars(
                select(RunTable).where((RunTable.workflow == workflow) | (RunTable.workflow_identity == workflow))
            ).all()
            if tenant_id:
                run_rows = [row for row in run_rows if row.request_id in request_ids]
            request_ids.update(row.request_id for row in run_rows)
            if not request_ids:
                return []
            event_rows = session.scalars(
                select(RequestEventTable)
                .where(RequestEventTable.request_id.in_(sorted(request_ids)))
                .order_by(RequestEventTable.timestamp)
            ).all()
            projection_rows = session.scalars(
                select(ProjectionMappingTable).where(
                    ProjectionMappingTable.entity_type == "request",
                    ProjectionMappingTable.entity_id.in_(sorted(request_ids)),
                )
            ).all()
            if tenant_id:
                projection_rows = [row for row in projection_rows if row.tenant_id == tenant_id]
            projection_by_id = {row.id: row for row in projection_rows}
            log_rows = (
                session.scalars(
                    select(ReconciliationLogTable)
                    .where(ReconciliationLogTable.projection_id.in_(list(projection_by_id.keys())))
                    .order_by(ReconciliationLogTable.created_at)
                ).all()
                if projection_by_id
                else []
            )
        entries = [
            AuditEntry(
                timestamp=row.timestamp.isoformat().replace("+00:00", "Z"),
                actor=row.actor,
                action=row.action,
                object_type=row.object_type,
                object_id=row.object_id,
                reason_or_evidence=row.reason_or_evidence,
                event_class="canonical",
                source_system="RGP",
                related_entity_type="workflow",
                related_entity_id=workflow,
                lineage=[f"workflow:{workflow}", f"request:{row.request_id}", f"{row.object_type}:{row.object_id}"],
            )
            for row in event_rows
        ]
        entries.extend(
            AuditEntry(
                timestamp=run_row.updated_at.isoformat().replace("+00:00", "Z"),
                actor="system",
                action="Run Status Snapshot",
                object_type="run",
                object_id=run_row.id,
                reason_or_evidence=f"status={run_row.status} request={run_row.request_id}",
                event_class="canonical",
                source_system="RGP",
                related_entity_type="workflow",
                related_entity_id=workflow,
                lineage=[f"workflow:{workflow}", f"request:{run_row.request_id}", f"run:{run_row.id}"],
            )
            for run_row in run_rows
        )
        entries.extend(
            AuditEntry(
                timestamp=log_row.created_at.isoformat().replace("+00:00", "Z"),
                actor=log_row.resolved_by or "system",
                action=self._audit_action_label(log_row.action, projection_row),
                object_type="projection",
                object_id=projection_row.id,
                reason_or_evidence=log_row.detail or f"{projection_row.external_system} {log_row.action}",
                event_class=self._audit_event_class(log_row.action),
                source_system=projection_row.external_system,
                integration_id=projection_row.integration_id,
                projection_id=projection_row.id,
                related_entity_type="workflow",
                related_entity_id=workflow,
                lineage=[
                    f"workflow:{workflow}",
                    f"{projection_row.entity_type}:{projection_row.entity_id}",
                    f"projection:{projection_row.id}",
                    f"external:{projection_row.external_system}",
                    *([f"external_ref:{projection_row.external_ref}"] if projection_row.external_ref else []),
                ],
            )
            for log_row in log_rows
            for projection_row in [projection_by_id.get(log_row.projection_id)]
            if projection_row is not None
        )
        entries = sorted(entries, key=lambda entry: entry.timestamp)
        if limit > 0:
            return entries[-limit:]
        return entries

    @staticmethod
    def _audit_event_class(action: str) -> str:
        normalized = action.lower()
        if normalized == "conflict":
            return "federated_conflict"
        if normalized in {"resolved", "merge", "retry_sync", "reprovision", "resume_session"}:
            return "federated_resolution"
        if normalized in {"created", "updated", "observed_external_state", "sync"}:
            return "federated_sync"
        return "federated_event"

    @staticmethod
    def _audit_action_label(action: str, projection_row: ProjectionMappingTable) -> str:
        normalized = action.lower()
        adapter_type = None
        if isinstance(projection_row.external_state, dict):
            adapter_type = projection_row.external_state.get("adapter_type")
        if normalized == "observed_external_state":
            return "Observed External State"
        if normalized == "conflict":
            return f"Conflict Detected ({adapter_type or projection_row.external_system})"
        if normalized == "resolved":
            return f"Reconciliation Applied ({adapter_type or projection_row.external_system})"
        return action.replace("_", " ").title()

    def list_policies(self, tenant_id: str | None = None) -> list[PolicyRecord]:
        with SessionLocal() as session:
            policy_stmt = select(PolicyTable)
            gate_stmt = select(TransitionGateTable).where(TransitionGateTable.active.is_(True))
            if tenant_id:
                policy_stmt = policy_stmt.where(PolicyTable.tenant_id == tenant_id)
                gate_stmt = gate_stmt.where(TransitionGateTable.tenant_id == tenant_id)
            rows = session.scalars(policy_stmt.order_by(desc(PolicyTable.updated_at))).all()
            gate_rows = session.scalars(gate_stmt.order_by(TransitionGateTable.gate_order)).all()
        rules_by_policy: dict[str, list[str]] = {}
        gates_by_policy: dict[str, list[dict[str, str]]] = {}
        for gate in gate_rows:
            rules_by_policy.setdefault(gate.policy_id, []).append(f"{gate.transition_target}: {gate.required_check_name}")
            gates_by_policy.setdefault(gate.policy_id, []).append(
                {
                    "transition_target": gate.transition_target,
                    "required_check_name": gate.required_check_name,
                }
            )
        return [
            PolicyRecord.model_validate(
                {
                    "id": row.id,
                    "name": row.name,
                    "status": row.status,
                    "scope": row.scope,
                    "rules": rules_by_policy.get(row.id, []),
                    "transition_gates": gates_by_policy.get(row.id, []),
                    "updated_at": row.updated_at.isoformat().replace("+00:00", "Z"),
                }
            )
            for row in rows
        ]

    def update_policy_rules(self, policy_id: str, payload: PolicyRuleUpdateRequest, tenant_id: str | None = None) -> PolicyRecord:
        with SessionLocal() as session:
            policy_row = session.get(PolicyTable, policy_id)
            if policy_row is None:
                raise StopIteration(policy_id)
            if tenant_id and policy_row.tenant_id != tenant_id:
                raise PermissionError(policy_id)
            existing_rows = session.scalars(select(TransitionGateTable).where(TransitionGateTable.policy_id == policy_id)).all()
            for row in existing_rows:
                session.delete(row)
            parsed_rules = policy_check_service.parse_request_transition_rules(payload.rules)
            for index, (transition_target, required_check_name) in enumerate(parsed_rules, start=1):
                session.add(
                    TransitionGateTable(
                        id=f"tg_{policy_id}_{index}",
                        tenant_id=policy_row.tenant_id,
                        policy_id=policy_id,
                        gate_scope="request",
                        transition_target=transition_target,
                        required_check_name=required_check_name,
                        gate_order=index,
                        active=True,
                    )
                )
            policy_row.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(policy_row)
            gate_rows = session.scalars(
                select(TransitionGateTable).where(TransitionGateTable.policy_id == policy_id, TransitionGateTable.active.is_(True)).order_by(TransitionGateTable.gate_order)
            ).all()
        return PolicyRecord.model_validate(
            {
                "id": policy_row.id,
                "name": policy_row.name,
                "status": policy_row.status,
                "scope": policy_row.scope,
                "rules": [f"{gate.transition_target}: {gate.required_check_name}" for gate in gate_rows],
                "transition_gates": [
                    {
                        "transition_target": gate.transition_target,
                        "required_check_name": gate.required_check_name,
                    }
                    for gate in gate_rows
                ],
                "updated_at": policy_row.updated_at.isoformat().replace("+00:00", "Z"),
            }
        )

    def list_request_check_runs(self, request_id: str, tenant_id: str | None = None) -> list[CheckRunRecord]:
        request = get_request_state(request_id, tenant_id) if tenant_id is not None else None
        if tenant_id is not None and request is None:
            raise StopIteration(request_id)
        if request is not None:
            from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

            dynamo_rows = DynamoDbGovernancePersistenceAdapter().list_request_check_runs(request_id, tenant_id=request.tenant_id)
            if dynamo_rows:
                return dynamo_rows
        with SessionLocal() as session:
            if request is None:
                self._ensure_request_access(session, request_id, tenant_id)
            rows = session.scalars(select(CheckRunTable).where(CheckRunTable.request_id == request_id).order_by(desc(CheckRunTable.queued_at))).all()
        return [self._check_run_from_row(row) for row in rows]

    def list_promotion_check_runs(self, promotion_id: str, tenant_id: str | None = None) -> list[CheckRunRecord]:
        with SessionLocal() as session:
            promotion_row = session.get(PromotionTable, promotion_id)
            if promotion_row is None:
                raise StopIteration(promotion_id)
            request_row = session.get(RequestTable, promotion_row.request_id)
            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
            elif tenant_id is not None and get_request_state(promotion_row.request_id, tenant_id) is None:
                raise StopIteration(promotion_row.request_id)
            rows = session.scalars(select(CheckRunTable).where(CheckRunTable.promotion_id == promotion_id).order_by(desc(CheckRunTable.queued_at))).all()
        return [self._check_run_from_row(row) for row in rows]

    def list_integrations(self, tenant_id: str | None = None) -> list[IntegrationRecord]:
        with SessionLocal() as session:
            stmt = select(IntegrationTable)
            if tenant_id:
                stmt = stmt.where(IntegrationTable.tenant_id == tenant_id)
            rows = session.scalars(stmt.order_by(IntegrationTable.name)).all()
        records: list[IntegrationRecord] = []
        for row in rows:
            resolved_endpoint = None
            if row.type == "runtime":
                try:
                    resolved_endpoint = runtime_dispatch_service.resolve_endpoint(row)
                except ValueError as exc:
                    resolved_endpoint = f"Invalid endpoint: {exc}"
            records.append(
                IntegrationRecord.model_validate(
                    {
                        "id": row.id,
                        "name": row.name,
                        "type": row.type,
                        "status": row.status,
                        "endpoint": row.endpoint,
                        "settings": integration_security_service.sanitize_settings_for_response(row.settings),
                        "has_api_key": integration_security_service.has_secret(row.settings, "api_key"),
                        "has_access_token": integration_security_service.has_secret(row.settings, "access_token"),
                        "resolved_endpoint": resolved_endpoint,
                        "supports_direct_assignment": row.type == "agent_runtime",
                        "supports_interactive_sessions": row.type == "agent_runtime",
                        "provider": self._provider_for_integration(row),
                    }
                )
            )
        return records

    def list_agent_integrations_for_request(self, request_id: str, tenant_id: str | None = None) -> list[IntegrationRecord]:
        if tenant_id is not None and get_request_state(request_id, tenant_id) is None:
            raise StopIteration(request_id)
        return [item for item in self.list_integrations(tenant_id) if item.supports_direct_assignment and item.supports_interactive_sessions]

    def preview_agent_assignment_context(
        self,
        request_id: str,
        integration_id: str,
        collaboration_mode: str = "agent_assisted",
        agent_operating_profile: str = "general",
        tenant_id: str | None = None,
    ) -> AgentSessionContextDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        request = get_request_state(request_id, tenant_id)
        if request is None:
            raise StopIteration(request_id)
        with SessionLocal() as session:
            integration_row = session.get(IntegrationTable, integration_id)
            if integration_row is None or integration_row.tenant_id != request.tenant_id:
                raise StopIteration(integration_id)
        bundle = context_bundle_service.preview_bundle(
            request_id=request_id,
            session_id=None,
            bundle_type="assignment_preview",
            assembled_by="system",
            tenant_id=request.tenant_id,
        )
        tools, restricted_tools, degraded_tools, warnings = self._build_agent_session_tools(
            integration_row=integration_row,
            bundle=bundle,
            collaboration_mode=collaboration_mode,
            agent_operating_profile=agent_operating_profile,
        )
        runtime_subtype = self._runtime_subtype_for_integration(integration_row)
        session_kind = self._session_kind_for_integration(integration_row)
        bundle.contents = {
            **(bundle.contents or {}),
            "available_tools": [tool.model_dump(mode="json") for tool in tools],
            "restricted_tools": [tool.model_dump(mode="json") for tool in restricted_tools],
            "degraded_tools": [tool.model_dump(mode="json") for tool in degraded_tools],
            "external_bindings": [
                {
                    "integration_id": integration_row.id,
                    "integration_name": integration_row.name,
                    "provider": self._provider_for_integration(integration_row),
                    "endpoint": integration_security_service.setting(integration_row, "base_url") or integration_row.endpoint,
                    "runtime_subtype": runtime_subtype,
                    "session_kind": session_kind,
                }
            ],
            **({
                "sbcl_agent_runtime": {
                    "environment_ref": f"environment:{request_id}",
                    "thread_ref": f"thread:{request_id}",
                    "turn_ref": f"turn:{request_id}:preview",
                    "pending_approval_count": 0,
                    "pending_artifact_count": 0,
                }
            } if runtime_subtype == "sbcl_agent" else {}),
        }
        bundle.policy_scope = {
            "collaboration_mode": collaboration_mode,
            "agent_operating_profile": agent_operating_profile,
            "tool_names": [tool.name for tool in tools],
            "restricted_tool_names": [tool.name for tool in restricted_tools],
            "degraded_tool_names": [tool.name for tool in degraded_tools],
            "warnings": warnings,
        }
        preview_row = AgentSessionTable(
            id=f"preview_{request_id}",
            tenant_id=bundle.tenant_id,
            request_id=request_id,
            integration_id=integration_row.id,
            agent_label=integration_row.name,
            collaboration_mode=collaboration_mode,
            agent_operating_profile=agent_operating_profile,
            status="preview",
            awaiting_human=False,
            summary="Previewing governed agent assignment context",
            external_session_ref=None,
            resume_request_status=None,
            assigned_by=actor_id,
            assigned_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return AgentSessionContextDetail(
            bundle=bundle,
            governed_runtime=self._governed_runtime_summary(preview_row, integration_row, bundle),
            available_tools=tools,
            restricted_tools=restricted_tools,
            degraded_tools=degraded_tools,
            capability_warnings=warnings,
            access_log=[],
        )

    def assign_agent_session(self, request_id: str, payload: AssignAgentSessionRequest, tenant_id: str | None = None) -> AgentSessionRecord:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        request = get_request_state(request_id, tenant_id)
        if request is None:
            raise StopIteration(request_id)
        with SessionLocal() as session:
            request_row = session.get(RequestTable, request_id)
            integration_row = session.get(IntegrationTable, payload.integration_id)
            if integration_row is None or integration_row.tenant_id != request.tenant_id:
                raise StopIteration(payload.integration_id)
            if integration_row.type != "agent_runtime":
                raise ValueError("Selected integration does not support direct interactive agent assignment")
            now = datetime.now(timezone.utc)
            session_id = f"ags_{request_id}_{int(now.timestamp())}"
            agent_label = payload.agent_label or integration_row.name
            runtime_subtype = self._runtime_subtype_for_integration(integration_row)
            session_row = AgentSessionTable(
                id=session_id,
                tenant_id=request.tenant_id,
                request_id=request_id,
                integration_id=integration_row.id,
                agent_label=agent_label,
                collaboration_mode=payload.collaboration_mode,
                agent_operating_profile=payload.agent_operating_profile,
                status="streaming",
                awaiting_human=False,
                summary=(f"{agent_label} is binding governed sbcl-agent runtime state" if runtime_subtype == "sbcl_agent" else f"{agent_label} is generating a response"),
                external_session_ref=None,
                resume_request_status=request.status.value if hasattr(request.status, "value") else str(request.status),
                assigned_by=payload.actor_id,
                assigned_at=now,
                updated_at=now + timedelta(seconds=1),
            )
            session.add(session_row)
            session.flush()
            if runtime_subtype == "sbcl_agent":
                session_row.external_session_ref = self._ensure_sbcl_agent_environment_ref(session_row, integration_row)
            kickoff_message = AgentSessionMessageTable(
                id=f"{session_id}_m001",
                tenant_id=request.tenant_id,
                session_id=session_id,
                request_id=request_id,
                sender_type="human",
                sender_id=payload.actor_id,
                message_type="assignment",
                body=payload.initial_prompt,
                created_at=now,
            )
            session.add(kickoff_message)
            agent_reply = AgentSessionMessageTable(
                id=f"{session_id}_m002",
                tenant_id=request.tenant_id,
                session_id=session_id,
                request_id=request_id,
                sender_type="agent",
                sender_id=integration_row.id,
                message_type="response",
                body="",
                created_at=now + timedelta(seconds=1),
            )
            session.add(agent_reply)
            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
                request_row.status = RequestStatus.AWAITING_INPUT.value
                request_row.updated_at = now
                request_row.updated_by = payload.actor_id
                request_row.version += 1
                self._append_event(
                    session=session,
                    request_id=request_id,
                    actor=payload.actor_id,
                    action="Agent Session Assigned",
                    reason_or_evidence=payload.reason,
                )
            event_store_service.append(
                session,
                tenant_id=request.tenant_id,
                event_type="agent_session.assigned",
                aggregate_type="agent_session",
                aggregate_id=session_id,
                request_id=request_id,
                actor=payload.actor_id,
                detail=payload.reason,
                payload={
                    "integration_id": integration_row.id,
                    "integration_name": integration_row.name,
                    "agent_label": agent_label,
                },
            )
            session.commit()
            if request_row is None:
                update_request_state(
                    request_id,
                    request.tenant_id,
                    payload.actor_id,
                    status=RequestStatus.AWAITING_INPUT,
                    updated_at=now,
                    updated_by=payload.actor_id,
                )
                record_request_event(
                    request_id,
                    request.tenant_id,
                    payload.actor_id,
                    "Agent Session Assigned",
                    payload.reason,
                    status=RequestStatus.AWAITING_INPUT.value,
                )
            if payload.collaboration_mode in {"agent_assisted", "agent_led"}:
                try:
                    current_mode = collaboration_mode_service.get_current_mode(request_id, request.tenant_id)
                    if current_mode != payload.collaboration_mode:
                        from app.models.collaboration import SwitchModeRequest

                        collaboration_mode_service.switch_mode(
                            request_id=request_id,
                            payload=SwitchModeRequest(
                                actor_id=payload.actor_id,
                                target_mode=payload.collaboration_mode,
                                reason="Agent session assignment selected collaboration mode",
                            ),
                            tenant_id=request.tenant_id,
                        )
                except ValueError:
                    pass
            self._refresh_agent_session_context(
                request_id=request_id,
                session_id=session_id,
                tenant_id=request.tenant_id,
                actor_id=payload.actor_id,
                integration_row=integration_row,
                collaboration_mode=payload.collaboration_mode,
                agent_operating_profile=payload.agent_operating_profile,
                session_row=session_row,
            )
            result = self._agent_session_from_row(session_row, integration_row, [kickoff_message, agent_reply])
        self._start_agent_session_turn_async(request_id, session_id, tenant_id)
        return result

    def get_agent_session(self, request_id: str, session_id: str, tenant_id: str | None = None) -> AgentSessionDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        request = get_request_state(request_id, tenant_id)
        if request is None:
            raise StopIteration(request_id)
        with SessionLocal() as session:
            session_row = session.get(AgentSessionTable, session_id)
            if session_row is None or session_row.request_id != request_id or session_row.tenant_id != request.tenant_id:
                raise StopIteration(session_id)
            integration_row = session.get(IntegrationTable, session_row.integration_id)
            message_rows = session.scalars(
                select(AgentSessionMessageTable).where(AgentSessionMessageTable.session_id == session_id).order_by(AgentSessionMessageTable.created_at)
            ).all()
        bundle = None
        if self._runtime_subtype_for_integration(integration_row) == "sbcl_agent":
            bundle = self._refresh_agent_session_context(
                request_id=request_id,
                session_id=session_id,
                tenant_id=request.tenant_id,
                actor_id=session_row.assigned_by,
                integration_row=integration_row,
                collaboration_mode=session_row.collaboration_mode,
                agent_operating_profile=session_row.agent_operating_profile,
                session_row=session_row,
            )
        summary = self._agent_session_from_row(session_row, integration_row, message_rows)
        if bundle is not None:
            summary.governed_runtime = self._governed_runtime_summary(session_row, integration_row, bundle)
        return AgentSessionDetail(**summary.model_dump(), messages=[self._agent_message_from_row(row) for row in message_rows])

    def get_agent_session_context(
        self,
        request_id: str,
        session_id: str,
        tenant_id: str | None = None,
    ) -> AgentSessionContextDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        request = get_request_state(request_id, tenant_id)
        if request is None:
            raise StopIteration(request_id)
        with SessionLocal() as session:
            session_row = session.get(AgentSessionTable, session_id)
            if session_row is None or session_row.request_id != request_id or session_row.tenant_id != request.tenant_id:
                raise StopIteration(session_id)
            integration_row = session.get(IntegrationTable, session_row.integration_id)
            bundle_row = (
                session.query(ContextBundleTable)
                .filter(
                    ContextBundleTable.request_id == request_id,
                    ContextBundleTable.session_id == session_id,
                    ContextBundleTable.tenant_id == request.tenant_id,
                )
                .order_by(desc(ContextBundleTable.assembled_at))
                .first()
            )
            access_rows = []
            if bundle_row is not None:
                access_rows = (
                    session.query(ContextAccessLogTable)
                    .filter(ContextAccessLogTable.bundle_id == bundle_row.id)
                    .order_by(desc(ContextAccessLogTable.accessed_at))
                    .limit(25)
                    .all()
                )

        if bundle_row is None:
            bundle = self._refresh_agent_session_context(
                request_id=request_id,
                session_id=session_id,
                tenant_id=request.tenant_id,
                actor_id=session_row.assigned_by,
                integration_row=integration_row,
                collaboration_mode=session_row.collaboration_mode,
                agent_operating_profile=session_row.agent_operating_profile,
                session_row=session_row,
            )
            with SessionLocal() as refresh_session:
                refreshed_access_rows = (
                    refresh_session.query(ContextAccessLogTable)
                    .filter(ContextAccessLogTable.bundle_id == bundle.id)
                    .order_by(desc(ContextAccessLogTable.accessed_at))
                    .limit(25)
                    .all()
                )
            access_log = [ContextAccessLogRecord.model_validate(row) for row in refreshed_access_rows]
        else:
            if self._runtime_subtype_for_integration(integration_row) == "sbcl_agent":
                bundle = self._refresh_agent_session_context(
                    request_id=request_id,
                    session_id=session_id,
                    tenant_id=request.tenant_id,
                    actor_id=session_row.assigned_by,
                    integration_row=integration_row,
                    collaboration_mode=session_row.collaboration_mode,
                    agent_operating_profile=session_row.agent_operating_profile,
                    session_row=session_row,
                )
            else:
                bundle = ContextBundleRecord.model_validate(bundle_row)
            access_log = [ContextAccessLogRecord.model_validate(row) for row in access_rows]

        tools, restricted_tools, degraded_tools, warnings = self._build_agent_session_tools(
            integration_row=integration_row,
            bundle=bundle,
            collaboration_mode=session_row.collaboration_mode,
            agent_operating_profile=session_row.agent_operating_profile,
        )
        return AgentSessionContextDetail(
            bundle=bundle,
            governed_runtime=self._governed_runtime_summary(session_row, integration_row, bundle),
            available_tools=tools,
            restricted_tools=restricted_tools,
            degraded_tools=degraded_tools,
            capability_warnings=warnings,
            access_log=access_log,
        )

    @staticmethod
    def _resolve_agent_session_target_status(
        request,
        session_row: AgentSessionTable,
        explicit_target_status: str | None,
    ) -> str:
        target_status = explicit_target_status or session_row.resume_request_status
        if not target_status or target_status == RequestStatus.AWAITING_INPUT.value:
            target_status = RequestStatus.IN_EXECUTION.value if request.current_run_id else RequestStatus.PLANNED.value
        return target_status

    def _queue_agent_session_turn(
        self,
        session,
        *,
        request_id: str,
        tenant_id: str,
        session_row: AgentSessionTable,
        actor_id: str,
        message_type: str,
        body: str,
        streaming_summary: str,
    ) -> datetime:
        existing_count = session.scalar(
            select(func.count()).select_from(AgentSessionMessageTable).where(AgentSessionMessageTable.session_id == session_row.id)
        ) or 0
        now = datetime.now(timezone.utc)
        human_message = AgentSessionMessageTable(
            id=f"{session_row.id}_m{existing_count + 1:03d}",
            tenant_id=tenant_id,
            session_id=session_row.id,
            request_id=request_id,
            sender_type="human",
            sender_id=actor_id,
            message_type=message_type,
            body=body,
            created_at=now,
        )
        session.add(human_message)
        agent_message = AgentSessionMessageTable(
            id=f"{session_row.id}_m{existing_count + 2:03d}",
            tenant_id=tenant_id,
            session_id=session_row.id,
            request_id=request_id,
            sender_type="agent",
            sender_id=session_row.integration_id,
            message_type="response",
            body="",
            created_at=now + timedelta(seconds=1),
        )
        session.add(agent_message)
        session_row.status = "streaming"
        session_row.awaiting_human = False
        session_row.summary = streaming_summary
        session_row.updated_at = now + timedelta(seconds=1)
        return now

    def _infer_sbcl_agent_work_item_id(
        self,
        session_row: AgentSessionTable,
        integration_row: IntegrationTable | None,
    ) -> str:
        live_state = self._sbcl_agent_bundle_state(session_row, integration_row)
        approvals = [item for item in (live_state.get("approvals") or []) if isinstance(item, dict)]
        if len(approvals) != 1:
            raise ValueError("Runtime checkpoint action requires an explicit work_item_id when the governed runtime has zero or multiple pending approvals")
        work_item_id = approvals[0].get("id")
        if not isinstance(work_item_id, str) or not work_item_id.strip():
            raise ValueError("Unable to resolve governed runtime work item id from pending approvals")
        return work_item_id

    def post_agent_session_message(
        self,
        request_id: str,
        session_id: str,
        payload: AgentSessionMessageCreateRequest,
        tenant_id: str | None = None,
    ) -> AgentSessionDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        request = get_request_state(request_id, tenant_id)
        if request is None:
            raise StopIteration(request_id)
        with SessionLocal() as session:
            request_row = session.get(RequestTable, request_id)
            session_row = session.get(AgentSessionTable, session_id)
            if session_row is None or session_row.request_id != request_id or session_row.tenant_id != request.tenant_id:
                raise StopIteration(session_id)
            integration_row = session.get(IntegrationTable, session_row.integration_id)
            existing_count = session.scalar(
                select(func.count()).select_from(AgentSessionMessageTable).where(AgentSessionMessageTable.session_id == session_id)
            ) or 0
            now = datetime.now(timezone.utc)
            human_message = AgentSessionMessageTable(
                id=f"{session_id}_m{existing_count + 1:03d}",
                tenant_id=request.tenant_id,
                session_id=session_id,
                request_id=request_id,
                sender_type="human",
                sender_id=payload.actor_id,
                message_type=payload.message_type,
                body=payload.body,
                created_at=now,
            )
            session.add(human_message)
            agent_message = AgentSessionMessageTable(
                id=f"{session_id}_m{existing_count + 2:03d}",
                tenant_id=request.tenant_id,
                session_id=session_id,
                request_id=request_id,
                sender_type="agent",
                sender_id=session_row.integration_id,
                message_type="response",
                body="",
                created_at=now + timedelta(seconds=1),
            )
            session.add(agent_message)
            session_row.status = "streaming"
            session_row.awaiting_human = False
            session_row.summary = "Interactive agent response is streaming"
            session_row.updated_at = now + timedelta(seconds=1)
            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
                request_row.status = RequestStatus.AWAITING_INPUT.value
                request_row.updated_at = now
                request_row.updated_by = payload.actor_id
                request_row.version += 1
                self._append_event(
                    session=session,
                    request_id=request_id,
                    actor=payload.actor_id,
                    action="Agent Session Message Posted",
                    reason_or_evidence=payload.reason,
                )
            event_store_service.append(
                session,
                tenant_id=request.tenant_id,
                event_type="agent_session.message_posted",
                aggregate_type="agent_session",
                aggregate_id=session_id,
                request_id=request_id,
                actor=payload.actor_id,
                detail=payload.reason,
                payload={"message_type": payload.message_type},
            )
            session.commit()
            if request_row is None:
                update_request_state(
                    request_id,
                    request.tenant_id,
                    payload.actor_id,
                    status=RequestStatus.AWAITING_INPUT,
                    updated_at=now,
                    updated_by=payload.actor_id,
                )
                record_request_event(
                    request_id,
                    request.tenant_id,
                    payload.actor_id,
                    "Agent Session Message Posted",
                    payload.reason,
                    status=RequestStatus.AWAITING_INPUT.value,
                )
            self._refresh_agent_session_context(
                request_id=request_id,
                session_id=session_id,
                tenant_id=request.tenant_id,
                actor_id=payload.actor_id,
                integration_row=integration_row,
                collaboration_mode=session_row.collaboration_mode,
                agent_operating_profile=session_row.agent_operating_profile,
            )
        self._start_agent_session_turn_async(request_id, session_id, tenant_id)
        return self.get_agent_session(request_id, session_id, tenant_id)

    def update_agent_session_governance(
        self,
        request_id: str,
        session_id: str,
        payload: UpdateAgentSessionGovernanceRequest,
        tenant_id: str | None = None,
    ) -> AgentSessionDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        request = get_request_state(request_id, tenant_id)
        if request is None:
            raise StopIteration(request_id)
        with SessionLocal() as session:
            request_row = session.get(RequestTable, request_id)
            session_row = session.get(AgentSessionTable, session_id)
            if session_row is None or session_row.request_id != request_id or session_row.tenant_id != request.tenant_id:
                raise StopIteration(session_id)
            integration_row = session.get(IntegrationTable, session_row.integration_id)
            session_row.collaboration_mode = payload.collaboration_mode
            session_row.agent_operating_profile = payload.agent_operating_profile
            session_row.updated_at = datetime.now(timezone.utc)
            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
                self._append_event(
                    session=session,
                    request_id=request_id,
                    actor=payload.actor_id,
                    action="Agent Session Governance Updated",
                    reason_or_evidence=payload.reason,
                )
            event_store_service.append(
                session,
                tenant_id=request.tenant_id,
                event_type="agent_session.governance_updated",
                aggregate_type="agent_session",
                aggregate_id=session_id,
                request_id=request_id,
                actor=payload.actor_id,
                detail=payload.reason,
                payload={
                    "collaboration_mode": payload.collaboration_mode,
                    "agent_operating_profile": payload.agent_operating_profile,
                },
            )
            session.commit()
            if request_row is None:
                record_request_event(
                    request_id,
                    request.tenant_id,
                    payload.actor_id,
                    "Agent Session Governance Updated",
                    payload.reason,
                )
            try:
                current_mode = collaboration_mode_service.get_current_mode(request_id, request.tenant_id)
                if current_mode != payload.collaboration_mode:
                    from app.models.collaboration import SwitchModeRequest

                    collaboration_mode_service.switch_mode(
                        request_id=request_id,
                        payload=SwitchModeRequest(
                            actor_id=payload.actor_id,
                            target_mode=payload.collaboration_mode,
                                reason="Agent session governance updated collaboration mode",
                            ),
                            tenant_id=request.tenant_id,
                        )
            except ValueError:
                pass
            self._refresh_agent_session_context(
                request_id=request_id,
                session_id=session_id,
                tenant_id=request.tenant_id,
                actor_id=payload.actor_id,
                integration_row=integration_row,
                collaboration_mode=payload.collaboration_mode,
                agent_operating_profile=payload.agent_operating_profile,
            )
        return self.get_agent_session(request_id, session_id, tenant_id)

    def resume_agent_session_runtime(
        self,
        request_id: str,
        session_id: str,
        payload: ResumeAgentSessionRuntimeRequest,
        tenant_id: str | None = None,
    ) -> AgentSessionDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        request = get_request_state(request_id, tenant_id)
        if request is None:
            raise StopIteration(request_id)
        with SessionLocal() as session:
            request_row = session.get(RequestTable, request_id)
            session_row = session.get(AgentSessionTable, session_id)
            if session_row is None or session_row.request_id != request_id or session_row.tenant_id != request.tenant_id:
                raise StopIteration(session_id)
            if session_row.status == "streaming":
                raise ValueError("Cannot resume the runtime while the agent response is still streaming")
            integration_row = session.get(IntegrationTable, session_row.integration_id)
            if self._runtime_subtype_for_integration(integration_row) != "sbcl_agent":
                raise ValueError("Runtime resume is only supported for sbcl-agent governed runtime sessions")

            environment_ref = self._ensure_sbcl_agent_environment_ref(session_row, integration_row)
            if not environment_ref:
                raise ValueError("sbcl-agent environment binding is unavailable for this governed runtime session")
            runtime_result = runtime_dispatch_service.resume_sbcl_agent_session(
                environment_ref,
                payload.work_item_id,
                note=payload.note,
            )
            target_status = self._resolve_agent_session_target_status(request, session_row, payload.target_status)
            control_body = f"Resume governed runtime work item {payload.work_item_id}."
            if payload.note:
                control_body = f"{control_body} Note: {payload.note}"
            now = self._queue_agent_session_turn(
                session,
                request_id=request_id,
                tenant_id=request.tenant_id,
                session_row=session_row,
                actor_id=payload.actor_id,
                message_type="runtime_resume",
                body=control_body,
                streaming_summary="Governed sbcl-agent runtime continuation is streaming",
            )
            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
                request_row.status = target_status
                request_row.updated_at = now
                request_row.updated_by = payload.actor_id
                request_row.version += 1
                self._append_event(
                    session=session,
                    request_id=request_id,
                    actor=payload.actor_id,
                    action="Agent Runtime Resumed",
                    reason_or_evidence=payload.reason,
                )
            event_store_service.append(
                session,
                tenant_id=request.tenant_id,
                event_type="agent_session.runtime_resumed",
                aggregate_type="agent_session",
                aggregate_id=session_id,
                request_id=request_id,
                actor=payload.actor_id,
                detail=payload.reason,
                payload={
                    "work_item_id": payload.work_item_id,
                    "target_status": target_status,
                    "note": payload.note,
                    "runtime_subtype": "sbcl_agent",
                    "runtime_result": runtime_result,
                },
            )
            session.commit()
            if request_row is None:
                update_request_state(
                    request_id,
                    request.tenant_id,
                    payload.actor_id,
                    status=RequestStatus(target_status),
                    updated_at=now,
                    updated_by=payload.actor_id,
                )
                record_request_event(
                    request_id,
                    request.tenant_id,
                    payload.actor_id,
                    "Agent Runtime Resumed",
                    payload.reason,
                    status=target_status,
                )
            self._refresh_agent_session_context(
                request_id=request_id,
                session_id=session_id,
                tenant_id=request.tenant_id,
                actor_id=payload.actor_id,
                integration_row=integration_row,
                collaboration_mode=session_row.collaboration_mode,
                agent_operating_profile=session_row.agent_operating_profile,
                session_row=session_row,
            )
        self._start_agent_session_turn_async(request_id, session_id, tenant_id)
        return self.get_agent_session(request_id, session_id, tenant_id)

    def approve_agent_session_checkpoint(
        self,
        request_id: str,
        session_id: str,
        payload: ApproveAgentSessionCheckpointRequest,
        tenant_id: str | None = None,
    ) -> AgentSessionDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        request = get_request_state(request_id, tenant_id)
        if request is None:
            raise StopIteration(request_id)
        with SessionLocal() as session:
            request_row = session.get(RequestTable, request_id)
            session_row = session.get(AgentSessionTable, session_id)
            if session_row is None or session_row.request_id != request_id or session_row.tenant_id != request.tenant_id:
                raise StopIteration(session_id)
            if session_row.status == "streaming":
                raise ValueError("Cannot approve the runtime checkpoint while the agent response is still streaming")
            integration_row = session.get(IntegrationTable, session_row.integration_id)
            if self._runtime_subtype_for_integration(integration_row) != "sbcl_agent":
                raise ValueError("Runtime checkpoint approval is only supported for sbcl-agent governed runtime sessions")

            environment_ref = self._ensure_sbcl_agent_environment_ref(session_row, integration_row)
            if not environment_ref:
                raise ValueError("sbcl-agent environment binding is unavailable for this governed runtime session")
            runtime_result = runtime_dispatch_service.approve_sbcl_agent_checkpoint(
                environment_ref,
                payload.work_item_id,
                policy=payload.policy,
                reason=payload.reason,
            )
            target_status = self._resolve_agent_session_target_status(request, session_row, payload.target_status)
            control_body = (
                f"Approve governed runtime checkpoint {payload.work_item_id} "
                f"under policy {payload.policy}."
            )
            now = self._queue_agent_session_turn(
                session,
                request_id=request_id,
                tenant_id=request.tenant_id,
                session_row=session_row,
                actor_id=payload.actor_id,
                message_type="runtime_approval",
                body=control_body,
                streaming_summary="Governed sbcl-agent checkpoint approval is being reconciled",
            )
            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
                request_row.status = target_status
                request_row.updated_at = now
                request_row.updated_by = payload.actor_id
                request_row.version += 1
                self._append_event(
                    session=session,
                    request_id=request_id,
                    actor=payload.actor_id,
                    action="Agent Runtime Checkpoint Approved",
                    reason_or_evidence=payload.reason,
                )
            event_store_service.append(
                session,
                tenant_id=request.tenant_id,
                event_type="agent_session.runtime_checkpoint_approved",
                aggregate_type="agent_session",
                aggregate_id=session_id,
                request_id=request_id,
                actor=payload.actor_id,
                detail=payload.reason,
                payload={
                    "work_item_id": payload.work_item_id,
                    "policy": payload.policy,
                    "target_status": target_status,
                    "runtime_subtype": "sbcl_agent",
                    "runtime_result": runtime_result,
                },
            )
            session.commit()
            if request_row is None:
                update_request_state(
                    request_id,
                    request.tenant_id,
                    payload.actor_id,
                    status=RequestStatus(target_status),
                    updated_at=now,
                    updated_by=payload.actor_id,
                )
                record_request_event(
                    request_id,
                    request.tenant_id,
                    payload.actor_id,
                    "Agent Runtime Checkpoint Approved",
                    payload.reason,
                    status=target_status,
                )
            self._refresh_agent_session_context(
                request_id=request_id,
                session_id=session_id,
                tenant_id=request.tenant_id,
                actor_id=payload.actor_id,
                integration_row=integration_row,
                collaboration_mode=session_row.collaboration_mode,
                agent_operating_profile=session_row.agent_operating_profile,
                session_row=session_row,
            )
        self._start_agent_session_turn_async(request_id, session_id, tenant_id)
        return self.get_agent_session(request_id, session_id, tenant_id)

    def complete_agent_session(
        self,
        request_id: str,
        session_id: str,
        payload: CompleteAgentSessionRequest,
        tenant_id: str | None = None,
    ) -> AgentSessionDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        request = get_request_state(request_id, tenant_id)
        if request is None:
            raise StopIteration(request_id)
        completion_action = (payload.completion_action or "accept_response").strip().lower()
        if completion_action == "resume_runtime":
            with SessionLocal() as session:
                session_row = session.get(AgentSessionTable, session_id)
                if session_row is None or session_row.request_id != request_id or session_row.tenant_id != request.tenant_id:
                    raise StopIteration(session_id)
                integration_row = session.get(IntegrationTable, session_row.integration_id)
                work_item_id = self._infer_sbcl_agent_work_item_id(session_row, integration_row)
            return self.resume_agent_session_runtime(
                request_id,
                session_id,
                ResumeAgentSessionRuntimeRequest(
                    actor_id=payload.actor_id,
                    work_item_id=work_item_id,
                    target_status=payload.target_status,
                    reason=payload.reason,
                ),
                tenant_id,
            )
        if completion_action == "approve_runtime_checkpoint":
            with SessionLocal() as session:
                session_row = session.get(AgentSessionTable, session_id)
                if session_row is None or session_row.request_id != request_id or session_row.tenant_id != request.tenant_id:
                    raise StopIteration(session_id)
                integration_row = session.get(IntegrationTable, session_row.integration_id)
                work_item_id = self._infer_sbcl_agent_work_item_id(session_row, integration_row)
            return self.approve_agent_session_checkpoint(
                request_id,
                session_id,
                ApproveAgentSessionCheckpointRequest(
                    actor_id=payload.actor_id,
                    work_item_id=work_item_id,
                    target_status=payload.target_status,
                    reason=payload.reason,
                ),
                tenant_id,
            )
        with SessionLocal() as session:
            request_row = session.get(RequestTable, request_id)
            session_row = session.get(AgentSessionTable, session_id)
            if session_row is None or session_row.request_id != request_id or session_row.tenant_id != request.tenant_id:
                raise StopIteration(session_id)
            if session_row.status == "streaming":
                raise ValueError("Cannot accept the session while the agent response is still streaming")
            integration_row = session.get(IntegrationTable, session_row.integration_id)
            runtime_subtype = self._runtime_subtype_for_integration(integration_row)
            target_status = self._resolve_agent_session_target_status(request, session_row, payload.target_status)

            session_row.status = "completed"
            session_row.awaiting_human = False
            session_row.summary = f"Accepted response and resumed {target_status.replace('_', ' ')}"
            event_type = "agent_session.completed"
            action_label = "Agent Session Completed"
            session_row.updated_at = datetime.now(timezone.utc)

            if request_row is not None:
                self._ensure_request_tenant_access(request_row, tenant_id)
                request_row.status = target_status
                request_row.updated_at = datetime.now(timezone.utc)
                request_row.updated_by = payload.actor_id
                request_row.version += 1

                self._append_event(
                    session=session,
                    request_id=request_id,
                    actor=payload.actor_id,
                    action=action_label,
                    reason_or_evidence=payload.reason,
                )
            event_store_service.append(
                session,
                tenant_id=request.tenant_id,
                event_type=event_type,
                aggregate_type="agent_session",
                aggregate_id=session_id,
                request_id=request_id,
                actor=payload.actor_id,
                detail=payload.reason,
                payload={"target_status": target_status, "completion_action": completion_action, "runtime_subtype": runtime_subtype},
            )
            session.commit()
            if request_row is None:
                update_request_state(
                    request_id,
                    request.tenant_id,
                    payload.actor_id,
                    status=RequestStatus(target_status),
                    updated_by=payload.actor_id,
                )
                record_request_event(
                    request_id,
                    request.tenant_id,
                    payload.actor_id,
                    action_label,
                    payload.reason,
                    status=target_status,
                )
        return self.get_agent_session(request_id, session_id, tenant_id)

    def stream_agent_session_response(
        self,
        request_id: str,
        session_id: str,
        tenant_id: str | None = None,
    ):
        snapshot = self.get_agent_session(request_id, session_id, tenant_id)
        yield {"event": "snapshot", "data": snapshot.model_dump(mode="json")}

        last_body = snapshot.latest_message.body if snapshot.latest_message and snapshot.latest_message.sender_type == "agent" else ""
        last_message_id = snapshot.latest_message.id if snapshot.latest_message and snapshot.latest_message.sender_type == "agent" else None
        if snapshot.status != "streaming":
            return

        self._start_agent_session_turn_async(request_id, session_id, tenant_id)
        while True:
            time.sleep(0.25)
            current = self.get_agent_session(request_id, session_id, tenant_id)
            current_agent_message = next((message for message in reversed(current.messages) if message.sender_type == "agent"), None)
            current_body = current_agent_message.body if current_agent_message else ""
            current_message_id = current_agent_message.id if current_agent_message else None
            if current_message_id != last_message_id:
                last_message_id = current_message_id
                last_body = ""
            if current_body != last_body:
                delta = current_body[len(last_body):] if current_body.startswith(last_body) else current_body
                yield {
                    "event": "delta",
                    "data": {
                        "session_id": session_id,
                        "message_id": current_message_id,
                        "delta": delta,
                        "body": current_body,
                        "done": current.status != "streaming",
                    },
                }
                last_body = current_body
            if current.status == "waiting_on_human":
                yield {"event": "done", "data": current.model_dump(mode="json")}
                return
            if current.status == "failed":
                yield {"event": "error", "data": {"message": current.summary}}
                return

    def _start_agent_session_turn_async(self, request_id: str, session_id: str, tenant_id: str | None = None) -> None:
        with self._agent_stream_lock:
            if session_id in self._agent_stream_inflight:
                return
            self._agent_stream_inflight.add(session_id)

        def _runner() -> None:
            try:
                self._execute_agent_session_turn(request_id, session_id, tenant_id)
            finally:
                with self._agent_stream_lock:
                    self._agent_stream_inflight.discard(session_id)

        threading.Thread(target=_runner, name=f"rgp-agent-{session_id}", daemon=True).start()

    def _execute_agent_session_turn(self, request_id: str, session_id: str, tenant_id: str | None = None) -> None:
        try:
            with SessionLocal() as session:
                session_row = session.get(AgentSessionTable, session_id)
                if session_row is None or session_row.request_id != request_id:
                    raise StopIteration(session_id)
                effective_tenant_id = tenant_id or session_row.tenant_id
                request = get_request_state(request_id, effective_tenant_id)
                if request is None or session_row.tenant_id != request.tenant_id:
                    raise StopIteration(request_id)
                if session_row.status != "streaming":
                    return
                integration_row = session.get(IntegrationTable, session_row.integration_id)
                message_rows = session.scalars(
                    select(AgentSessionMessageTable).where(AgentSessionMessageTable.session_id == session_id).order_by(AgentSessionMessageTable.created_at)
                ).all()
                if not message_rows:
                    raise ValueError("Agent session has no transcript")
                pending_agent_message = next((row for row in reversed(message_rows) if row.sender_type == "agent"), None)
                latest_human_message = next((row for row in reversed(message_rows) if row.sender_type == "human"), None)
                if pending_agent_message is None or latest_human_message is None:
                    raise ValueError("Agent session transcript is incomplete")

                transcript_rows = [row for row in message_rows if row.id != pending_agent_message.id]
                bundle_row = (
                    session.query(ContextBundleTable)
                    .filter(
                        ContextBundleTable.request_id == request_id,
                        ContextBundleTable.session_id == session_id,
                        ContextBundleTable.tenant_id == request.tenant_id,
                    )
                    .order_by(desc(ContextBundleTable.assembled_at))
                    .first()
                )
                if bundle_row is not None:
                    context_bundle_service.record_access(
                        bundle_id=bundle_row.id,
                        accessor_type="agent",
                        accessor_id=integration_row.id,
                        resource="agent_session_turn",
                        result="granted",
                        policy_basis=bundle_row.policy_scope or {},
                    )
                context_bundle = ContextBundleRecord.model_validate(bundle_row) if bundle_row is not None else None
                available_tools = []
                restricted_tools = []
                degraded_tools = []
                if context_bundle is not None:
                    available_tools = [
                        tool
                        for tool in ((context_bundle.contents or {}).get("available_tools", []) if isinstance(context_bundle.contents, dict) else [])
                        if isinstance(tool, dict)
                    ]
                    restricted_tools = [
                        tool
                        for tool in ((context_bundle.contents or {}).get("restricted_tools", []) if isinstance(context_bundle.contents, dict) else [])
                        if isinstance(tool, dict)
                    ]
                    degraded_tools = [
                        tool
                        for tool in ((context_bundle.contents or {}).get("degraded_tools", []) if isinstance(context_bundle.contents, dict) else [])
                        if isinstance(tool, dict)
                    ]
                    for tool in available_tools:
                        context_bundle_service.record_access(
                            bundle_id=bundle_row.id,
                            accessor_type="agent",
                            accessor_id=integration_row.id,
                            resource=f"mcp_tool:{tool.get('name', 'unknown')}",
                            result="granted",
                            policy_basis={
                                **(bundle_row.policy_scope or {}),
                                "availability": "available",
                            },
                        )
                    for tool in degraded_tools:
                        context_bundle_service.record_access(
                            bundle_id=bundle_row.id,
                            accessor_type="agent",
                            accessor_id=integration_row.id,
                            resource=f"mcp_tool:{tool.get('name', 'unknown')}",
                            result="degraded",
                            policy_basis={
                                **(bundle_row.policy_scope or {}),
                                "availability": "degraded",
                                "reason": tool.get("availability_reason"),
                            },
                        )
                    for tool in restricted_tools:
                        context_bundle_service.record_access(
                            bundle_id=bundle_row.id,
                            accessor_type="agent",
                            accessor_id=integration_row.id,
                            resource=f"mcp_tool:{tool.get('name', 'unknown')}",
                            result="denied",
                            policy_basis={
                                **(bundle_row.policy_scope or {}),
                                "availability": "denied",
                                "reason": tool.get("availability_reason"),
                            },
                        )
                runtime_subtype = self._runtime_subtype_for_integration(integration_row)
                if runtime_subtype == "sbcl_agent":
                    context_bundle = self._refresh_agent_session_context(
                        request_id=request_id,
                        session_id=session_id,
                        tenant_id=request.tenant_id,
                        actor_id=session_row.assigned_by,
                        integration_row=integration_row,
                        collaboration_mode=session_row.collaboration_mode,
                        agent_operating_profile=session_row.agent_operating_profile,
                        session_row=session_row,
                    )
                    pending_agent_message.body = self._sbcl_agent_response_text(
                        session_row,
                        latest_human_message,
                        context_bundle,
                    )
                    session_row.external_session_ref = self._ensure_sbcl_agent_environment_ref(session_row, integration_row)
                    session_row.updated_at = datetime.now(timezone.utc)
                    session.flush()
                    session.commit()

                    transitioned_at = datetime.now(timezone.utc)
                    transition_result = session.execute(
                        update(AgentSessionTable)
                        .where(
                            AgentSessionTable.id == session_id,
                            AgentSessionTable.status == "streaming",
                        )
                        .values(
                            status="waiting_on_human",
                            awaiting_human=True,
                            summary=self._sbcl_agent_turn_summary(session_row, context_bundle),
                            updated_at=transitioned_at,
                        )
                    )
                    if transition_result.rowcount == 0:
                        session.rollback()
                        return
                    session.commit()
                    return
                is_initial_turn = latest_human_message.message_type == "assignment" and session_row.external_session_ref is None
                if is_initial_turn:
                    provider_stream = agent_provider_service.stream_start_session(
                        integration=integration_row,
                        request_title=request.title,
                        initial_prompt=latest_human_message.body,
                        transcript=self._agent_transcript_from_rows(transcript_rows),
                        context_bundle=context_bundle,
                        available_tools=available_tools,
                    )
                else:
                    provider_stream = agent_provider_service.stream_continue_session(
                        integration=integration_row,
                        agent_label=session_row.agent_label,
                        transcript=self._agent_transcript_from_rows(transcript_rows),
                        latest_human_message=latest_human_message.body,
                        external_session_ref=session_row.external_session_ref,
                        context_bundle=context_bundle,
                        available_tools=available_tools,
                    )

                for chunk in provider_stream:
                    pending_agent_message.body = chunk.assistant_text
                    session_row.external_session_ref = chunk.external_session_ref or session_row.external_session_ref
                    session_row.updated_at = datetime.now(timezone.utc)
                    session.flush()
                    session.commit()

                transitioned_at = datetime.now(timezone.utc)
                transition_result = session.execute(
                    update(AgentSessionTable)
                    .where(
                        AgentSessionTable.id == session_id,
                        AgentSessionTable.status == "streaming",
                    )
                    .values(
                        status="waiting_on_human",
                        awaiting_human=True,
                        summary=f"{session_row.agent_label} requested follow-up guidance",
                        updated_at=transitioned_at,
                    )
                )
                if transition_result.rowcount == 0:
                    session.rollback()
                    return
                session.commit()
        except Exception as exc:
            with SessionLocal() as session:
                failure_result = session.execute(
                    update(AgentSessionTable)
                    .where(
                        AgentSessionTable.id == session_id,
                        AgentSessionTable.status == "streaming",
                    )
                    .values(
                        status="failed",
                        awaiting_human=True,
                        summary=f"Agent streaming failed: {exc}",
                        updated_at=datetime.now(timezone.utc),
                    )
                )
                if failure_result.rowcount == 0:
                    session.rollback()
                    return
                session.commit()

    def import_agent_session_artifact(
        self,
        request_id: str,
        session_id: str,
        payload: ImportAgentSessionArtifactRequest,
        tenant_id: str | None = None,
    ) -> ArtifactDetail:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        request = get_request_state(request_id, tenant_id)
        if request is None:
            raise StopIteration(request_id)
        now = datetime.now(timezone.utc)
        with SessionLocal() as session:
            session_row = session.get(AgentSessionTable, session_id)
            if session_row is None or session_row.request_id != request_id or session_row.tenant_id != request.tenant_id:
                raise StopIteration(session_id)
            integration_row = session.get(IntegrationTable, session_row.integration_id)
            if self._runtime_subtype_for_integration(integration_row) != "sbcl_agent":
                raise ValueError("Artifact import rules are currently specialized for sbcl-agent governed runtime sessions")
            artifact_id = f"art_{uuid4().hex[:12]}"
            version_id = f"av_{uuid4().hex[:12]}"
            content_ref = None
            if payload.content:
                content_ref = self._artifact_content_ref(artifact_id, version_id)
                object_store_service.put_text(content_ref, payload.content)
            defaults = self._artifact_import_defaults(payload)
            artifact_row = ArtifactTable(
                id=artifact_id,
                type=payload.artifact_type,
                name=payload.title,
                current_version="v1",
                status=defaults["status"],
                request_id=request_id,
                updated_at=now,
                owner=payload.actor_id,
                review_state=defaults["review_state"],
                promotion_relevant=defaults["promotion_relevant"],
                versions=[
                    {
                        "id": version_id,
                        "label": "v1",
                        "status": defaults["status"],
                        "created_at": now.isoformat().replace("+00:00", "Z"),
                        "author": payload.actor_id,
                        "summary": payload.summary,
                        "content": payload.content if payload.content and content_ref is None else None,
                        "content_ref": content_ref,
                        "path": payload.path,
                        "source_ref": payload.source_ref,
                        "image_ref": payload.image_ref,
                        "artifact_key": self._normalize_artifact_key(payload.artifact_key),
                        "import_rule": "sbcl_agent_governed_runtime",
                        "session_id": session_id,
                    }
                ],
                selected_version_id=version_id,
                stale_review=False,
            )
            session.add(artifact_row)
            session.flush()
            self._append_artifact_event(
                session,
                artifact_id=artifact_id,
                artifact_version_id=version_id,
                actor=payload.actor_id,
                action="imported_from_agent_session",
                detail=payload.reason,
            )
            self._append_artifact_lineage(
                session,
                artifact_id=artifact_id,
                from_version_id=(payload.source_ref or session_row.external_session_ref or session_id)[:64],
                to_version_id=version_id,
                relation="imported_from_sbcl_agent_session",
            )
            event_store_service.append(
                session,
                tenant_id=request.tenant_id,
                event_type="artifact.imported_from_agent_session",
                aggregate_type="artifact",
                aggregate_id=artifact_id,
                request_id=request_id,
                artifact_id=artifact_id,
                actor=payload.actor_id,
                detail=payload.reason,
                payload={"session_id": session_id, "artifact_key": payload.artifact_key, "runtime_subtype": "sbcl_agent"},
            )
            session.commit()
            session.refresh(artifact_row)
            event_rows = session.scalars(select(ArtifactEventTable).where(ArtifactEventTable.artifact_id == artifact_id).order_by(ArtifactEventTable.timestamp)).all()
            lineage_rows = session.scalars(select(ArtifactLineageEdgeTable).where(ArtifactLineageEdgeTable.artifact_id == artifact_id).order_by(ArtifactLineageEdgeTable.created_at)).all()
            return self._artifact_detail_from_row(artifact_row, event_rows, lineage_rows)

    def create_integration(self, payload: CreateIntegrationRequest, tenant_id: str) -> IntegrationRecord:
        with SessionLocal() as session:
            existing = session.get(IntegrationTable, payload.id)
            if existing is not None and existing.tenant_id == tenant_id:
                raise ValueError(f"Integration {payload.id} already exists")
            self._validate_integration_configuration(payload.type, payload.endpoint, payload.settings)
            session.add(
                IntegrationTable(
                    id=payload.id,
                    tenant_id=tenant_id,
                    name=payload.name,
                    type=payload.type,
                    status=payload.status,
                    endpoint=payload.endpoint,
                    settings=integration_security_service.prepare_settings_for_storage(None, payload.settings),
                )
            )
            session.commit()
        return next(item for item in self.list_integrations(tenant_id) if item.id == payload.id)

    def update_integration(self, integration_id: str, payload: UpdateIntegrationRequest, tenant_id: str) -> IntegrationRecord:
        with SessionLocal() as session:
            row = session.get(IntegrationTable, integration_id)
            if row is None or row.tenant_id != tenant_id:
                raise StopIteration(integration_id)
            merged_settings = integration_security_service.prepare_settings_for_storage(
                row.settings,
                payload.settings,
                clear_api_key=payload.clear_api_key,
                clear_access_token=payload.clear_access_token,
            )
            self._validate_integration_configuration(payload.type, payload.endpoint, merged_settings)
            row.name = payload.name
            row.type = payload.type
            row.status = payload.status
            row.endpoint = payload.endpoint
            row.settings = merged_settings
            session.commit()
        return next(item for item in self.list_integrations(tenant_id) if item.id == integration_id)

    def delete_integration(self, integration_id: str, tenant_id: str) -> None:
        with SessionLocal() as session:
            row = session.get(IntegrationTable, integration_id)
            if row is None or row.tenant_id != tenant_id:
                raise StopIteration(integration_id)
            session.delete(row)
            session.commit()

    def list_tenants(self) -> list[TenantRecord]:
        with SessionLocal() as session:
            tenant_rows = session.scalars(select(TenantTable).order_by(TenantTable.name)).all()
            organization_counts = {
                tenant_id: count
                for tenant_id, count in session.execute(
                    select(OrganizationTable.tenant_id, func.count(OrganizationTable.id)).group_by(OrganizationTable.tenant_id)
                ).all()
            }
        return [
            TenantRecord(
                id=row.id,
                name=row.name,
                status=row.status,
                organization_count=organization_counts.get(row.id, 0),
            )
            for row in tenant_rows
        ]

    def create_tenant(self, payload: CreateTenantRequest) -> TenantRecord:
        with SessionLocal() as session:
            existing = session.get(TenantTable, payload.id)
            if existing is not None:
                raise ValueError(f"Tenant {payload.id} already exists")
            now = datetime.now(timezone.utc)
            row = TenantTable(
                id=payload.id,
                name=payload.name,
                status=payload.status,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.commit()
        return TenantRecord(id=row.id, name=row.name, status=row.status, organization_count=0)

    def update_tenant(self, tenant_id: str, payload: UpdateTenantRequest) -> TenantRecord:
        with SessionLocal() as session:
            row = session.get(TenantTable, tenant_id)
            if row is None:
                raise StopIteration(tenant_id)
            row.name = payload.name
            row.status = payload.status
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
        return TenantRecord(id=row.id, name=row.name, status=row.status, organization_count=len(self.list_organizations(tenant_id)))

    def list_users(self, tenant_id: str | None = None) -> list[UserRecord]:
        with SessionLocal() as session:
            stmt = select(UserTable).order_by(UserTable.display_name)
            if tenant_id:
                stmt = stmt.where(UserTable.tenant_id == tenant_id)
            rows = session.scalars(stmt).all()
        return [
            UserRecord(
                id=row.id,
                tenant_id=row.tenant_id,
                display_name=row.display_name,
                email=row.email,
                role_summary=row.role_summary or [],
                status=row.status,
                has_password=bool(row.password_hash),
                password_reset_required=bool(row.password_reset_required),
                registration_request_id=row.registration_request_id,
            )
            for row in rows
        ]

    def create_user(self, payload: CreateUserRequest, tenant_id: str) -> UserRecord:
        with SessionLocal() as session:
            existing = session.get(UserTable, payload.id)
            if existing is not None and existing.tenant_id == tenant_id:
                raise ValueError(f"User {payload.id} already exists")
            now = datetime.now(timezone.utc)
            row = UserTable(
                id=payload.id,
                tenant_id=tenant_id,
                display_name=payload.display_name,
                email=payload.email,
                role_summary=payload.role_summary,
                status=payload.status,
                password_hash=local_account_service.hash_password(payload.password) if payload.password else None,
                password_reset_required=payload.password_reset_required if payload.password else True,
                registration_request_id=payload.registration_request_id,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.commit()
        return UserRecord(
            id=row.id,
            tenant_id=row.tenant_id,
            display_name=row.display_name,
            email=row.email,
            role_summary=row.role_summary or [],
            status=row.status,
            has_password=bool(row.password_hash),
            password_reset_required=bool(row.password_reset_required),
            registration_request_id=row.registration_request_id,
        )

    def update_user(self, user_id: str, payload: UpdateUserRequest, tenant_id: str) -> UserRecord:
        with SessionLocal() as session:
            row = session.get(UserTable, user_id)
            if row is None or row.tenant_id != tenant_id:
                raise StopIteration(user_id)
            row.display_name = payload.display_name
            row.email = payload.email
            row.role_summary = payload.role_summary
            row.status = payload.status
            if payload.reset_password:
                row.password_hash = None
                row.password_reset_required = True
            elif payload.password:
                row.password_hash = local_account_service.hash_password(payload.password)
                row.password_reset_required = payload.password_reset_required if payload.password_reset_required is not None else False
            elif payload.password_reset_required is not None:
                row.password_reset_required = payload.password_reset_required
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
        return UserRecord(
            id=row.id,
            tenant_id=row.tenant_id,
            display_name=row.display_name,
            email=row.email,
            role_summary=row.role_summary or [],
            status=row.status,
            has_password=bool(row.password_hash),
            password_reset_required=bool(row.password_reset_required),
            registration_request_id=row.registration_request_id,
        )

    def authenticate_local_user(self, email: str, password: str, tenant_id: str) -> Principal:
        with SessionLocal() as session:
            row = session.scalars(
                select(UserTable).where(
                    UserTable.tenant_id == tenant_id,
                    func.lower(UserTable.email) == email.strip().lower(),
                )
            ).first()
            if row is None or row.status != "active":
                raise ValueError("Invalid credentials")
            if row.password_reset_required:
                raise ValueError("Password reset is required before this account can sign in")
            if not local_account_service.verify_password(password, row.password_hash):
                raise ValueError("Invalid credentials")
        roles = [PrincipalRole(role) for role in (row.role_summary or []) if role in {item.value for item in PrincipalRole}]
        return Principal(user_id=row.id, tenant_id=row.tenant_id, roles=roles or [PrincipalRole.OBSERVER])

    def create_public_registration_request(self, payload: PublicRegistrationRequest) -> RegistrationSubmissionResponse:
        actor_id = "registration_portal"
        with SessionLocal() as validation_session:
            organization_row = validation_session.get(OrganizationTable, payload.organization_id)
            team_row = validation_session.get(TeamTable, payload.requested_team_id)
            if organization_row is None or organization_row.tenant_id != payload.tenant_id or organization_row.status != "active":
                raise ValueError("Select a valid active organization for this registration request")
            if team_row is None or team_row.tenant_id != payload.tenant_id or team_row.status != "active":
                raise ValueError("Select a valid active team for this registration request")
            if team_row.organization_id != organization_row.id:
                raise ValueError("Select a team that belongs to the chosen organization")
        draft = self.create_request_draft(
            CreateRequestDraft(
                template_id="tmpl_user_registration",
                template_version="1.0.0",
                title=f"Register User: {payload.display_name}",
                summary=f"External registration request for {payload.email}",
                priority=RequestPriority.MEDIUM,
                input_payload={
                    "display_name": payload.display_name,
                    "email": payload.email,
                    "organization_id": payload.organization_id,
                    "organization_name": organization_row.name,
                    "job_title": payload.job_title,
                    "requested_team_id": payload.requested_team_id,
                    "requested_roles": [role.value for role in payload.requested_roles],
                    "business_justification": payload.business_justification,
                },
            ),
            actor_id=actor_id,
            tenant_id=payload.tenant_id,
        )
        self.submit_request(draft.id, SubmitRequest(actor_id=actor_id, reason="Submitted from public registration portal"), payload.tenant_id)
        for target_status in (
            RequestStatus.VALIDATED,
            RequestStatus.CLASSIFIED,
            RequestStatus.OWNERSHIP_RESOLVED,
            RequestStatus.PLANNED,
            RequestStatus.QUEUED,
            RequestStatus.IN_EXECUTION,
            RequestStatus.AWAITING_REVIEW,
        ):
            while True:
                try:
                    self.transition_request(
                        draft.id,
                        TransitionRequest(actor_id=actor_id, target_status=target_status, reason="Fast-tracked registration intake"),
                        payload.tenant_id,
                    )
                    break
                except ValueError as exc:
                    message = str(exc)
                    if "queued or running" in message or "Automated evaluation queued" in message:
                        time.sleep(0.2)
                        continue
                    raise
        return RegistrationSubmissionResponse(
            request_id=draft.id,
            status=RequestStatus.AWAITING_REVIEW.value,
            message="Registration request submitted for administrative review.",
        )

    def list_organizations(self, tenant_id: str | None = None) -> list[OrganizationRecord]:
        with SessionLocal() as session:
            stmt = select(OrganizationTable).order_by(OrganizationTable.name)
            if tenant_id:
                stmt = stmt.where(OrganizationTable.tenant_id == tenant_id)
            rows = session.scalars(stmt).all()
        return [OrganizationRecord(id=row.id, tenant_id=row.tenant_id, name=row.name, status=row.status) for row in rows]

    def create_organization(self, payload: CreateOrganizationRequest, tenant_id: str) -> OrganizationRecord:
        organization_tenant_id = payload.tenant_id or tenant_id
        with SessionLocal() as session:
            existing = session.get(OrganizationTable, payload.id)
            if existing is not None and existing.tenant_id == organization_tenant_id:
                raise ValueError(f"Organization {payload.id} already exists")
            now = datetime.now(timezone.utc)
            row = OrganizationTable(
                id=payload.id,
                tenant_id=organization_tenant_id,
                name=payload.name,
                status=payload.status,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.commit()
        return OrganizationRecord(id=row.id, tenant_id=row.tenant_id, name=row.name, status=row.status)

    def update_organization(self, organization_id: str, payload: UpdateOrganizationRequest, tenant_id: str) -> OrganizationRecord:
        with SessionLocal() as session:
            row = session.get(OrganizationTable, organization_id)
            if row is None or row.tenant_id != tenant_id:
                raise StopIteration(organization_id)
            row.name = payload.name
            row.status = payload.status
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
        return OrganizationRecord(id=row.id, tenant_id=row.tenant_id, name=row.name, status=row.status)

    def list_teams(self, tenant_id: str | None = None) -> list[TeamRecord]:
        with SessionLocal() as session:
            organization_stmt = select(OrganizationTable)
            team_stmt = select(TeamTable).order_by(TeamTable.name)
            membership_stmt = select(TeamMembershipTable)
            user_stmt = select(UserTable)
            if tenant_id:
                organization_stmt = organization_stmt.where(OrganizationTable.tenant_id == tenant_id)
                team_stmt = team_stmt.where(TeamTable.tenant_id == tenant_id)
                membership_stmt = membership_stmt.where(TeamMembershipTable.tenant_id == tenant_id)
                user_stmt = user_stmt.where(UserTable.tenant_id == tenant_id)
            organization_rows = {row.id: row for row in session.scalars(organization_stmt).all()}
            team_rows = session.scalars(team_stmt).all()
            membership_rows = session.scalars(membership_stmt).all()
            user_rows = {row.id: row for row in session.scalars(user_stmt).all()}
        memberships_by_team: dict[str, list[TeamMemberRecord]] = {}
        for membership in membership_rows:
            user = user_rows.get(membership.user_id)
            if not user:
                continue
            memberships_by_team.setdefault(membership.team_id, []).append(
                TeamMemberRecord(
                    user_id=user.id,
                    display_name=user.display_name,
                    email=user.email,
                    role=membership.role,
                )
            )
        return [
            TeamRecord(
                id=row.id,
                tenant_id=row.tenant_id,
                organization_id=row.organization_id,
                organization_name=organization_rows.get(row.organization_id).name if organization_rows.get(row.organization_id) else row.organization_id,
                name=row.name,
                kind=row.kind,
                status=row.status,
                member_count=len(memberships_by_team.get(row.id, [])),
                members=sorted(memberships_by_team.get(row.id, []), key=lambda member: member.display_name),
            )
            for row in team_rows
        ]

    def create_team(self, payload: CreateTeamRequest, tenant_id: str) -> TeamRecord:
        with SessionLocal() as session:
            existing = session.get(TeamTable, payload.id)
            if existing is not None and existing.tenant_id == tenant_id:
                raise ValueError(f"Team {payload.id} already exists")
            organization = session.get(OrganizationTable, payload.organization_id)
            if organization is None or organization.tenant_id != tenant_id:
                raise StopIteration(payload.organization_id)
            now = datetime.now(timezone.utc)
            row = TeamTable(
                id=payload.id,
                tenant_id=tenant_id,
                organization_id=payload.organization_id,
                name=payload.name,
                kind=payload.kind,
                status=payload.status,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.commit()
        return TeamRecord(
            id=row.id,
            tenant_id=row.tenant_id,
            organization_id=row.organization_id,
            organization_name=organization.name,
            name=row.name,
            kind=row.kind,
            status=row.status,
            member_count=0,
            members=[],
        )

    def update_team(self, team_id: str, payload: UpdateTeamRequest, tenant_id: str) -> TeamRecord:
        with SessionLocal() as session:
            row = session.get(TeamTable, team_id)
            if row is None or row.tenant_id != tenant_id:
                raise StopIteration(team_id)
            organization = session.get(OrganizationTable, payload.organization_id)
            if organization is None or organization.tenant_id != tenant_id:
                raise StopIteration(payload.organization_id)
            row.organization_id = payload.organization_id
            row.name = payload.name
            row.kind = payload.kind
            row.status = payload.status
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
        return next(team for team in self.list_teams(tenant_id) if team.id == team_id)

    def add_team_membership(self, payload: AddTeamMembershipRequest, tenant_id: str) -> TeamRecord:
        with SessionLocal() as session:
            team_row = session.get(TeamTable, payload.team_id)
            user_row = session.get(UserTable, payload.user_id)
            if team_row is None or team_row.tenant_id != tenant_id:
                raise StopIteration(payload.team_id)
            if user_row is None or user_row.tenant_id != tenant_id:
                raise StopIteration(payload.user_id)
            existing = session.scalars(
                select(TeamMembershipTable).where(
                    TeamMembershipTable.tenant_id == tenant_id,
                    TeamMembershipTable.team_id == payload.team_id,
                    TeamMembershipTable.user_id == payload.user_id,
                )
            ).first()
            if existing is None:
                now = datetime.now(timezone.utc)
                session.add(
                    TeamMembershipTable(
                        id=f"tm_{payload.team_id}_{payload.user_id}",
                        tenant_id=tenant_id,
                        team_id=payload.team_id,
                        user_id=payload.user_id,
                        role=payload.role,
                        created_at=now,
                    )
                )
            else:
                existing.role = payload.role
            session.commit()
        return next(team for team in self.list_teams(tenant_id) if team.id == payload.team_id)

    def list_portfolios(self, tenant_id: str | None = None) -> list[PortfolioRecord]:
        with SessionLocal() as session:
            portfolio_stmt = select(PortfolioTable).order_by(PortfolioTable.name)
            scope_stmt = select(PortfolioScopeTable).order_by(PortfolioScopeTable.scope_key)
            if tenant_id:
                portfolio_stmt = portfolio_stmt.where(PortfolioTable.tenant_id == tenant_id)
                scope_stmt = scope_stmt.where(PortfolioScopeTable.tenant_id == tenant_id)
            portfolio_rows = session.scalars(portfolio_stmt).all()
            scope_rows = session.scalars(scope_stmt).all()
        scopes_by_portfolio: dict[str, list[str]] = {}
        for scope in scope_rows:
            scopes_by_portfolio.setdefault(scope.portfolio_id, []).append(scope.scope_key)
        return [
            PortfolioRecord(
                id=row.id,
                tenant_id=row.tenant_id,
                name=row.name,
                status=row.status,
                owner_team_id=row.owner_team_id,
                scope_keys=scopes_by_portfolio.get(row.id, []),
            )
            for row in portfolio_rows
        ]

    def create_portfolio(self, payload: CreatePortfolioRequest, tenant_id: str) -> PortfolioRecord:
        with SessionLocal() as session:
            existing = session.get(PortfolioTable, payload.id)
            if existing is not None and existing.tenant_id == tenant_id:
                raise ValueError(f"Portfolio {payload.id} already exists")
            owner_team = session.get(TeamTable, payload.owner_team_id)
            if owner_team is None or owner_team.tenant_id != tenant_id:
                raise StopIteration(payload.owner_team_id)
            now = datetime.now(timezone.utc)
            session.add(
                PortfolioTable(
                    id=payload.id,
                    tenant_id=tenant_id,
                    name=payload.name,
                    status=payload.status,
                    owner_team_id=payload.owner_team_id,
                    created_at=now,
                    updated_at=now,
                )
            )
            for index, scope_key in enumerate(payload.scope_keys, start=1):
                session.add(
                    PortfolioScopeTable(
                        id=f"ps_{payload.id}_{index}",
                        tenant_id=tenant_id,
                        portfolio_id=payload.id,
                        scope_type="team",
                        scope_key=scope_key,
                    )
                )
            session.commit()
        return next(portfolio for portfolio in self.list_portfolios(tenant_id) if portfolio.id == payload.id)

    def list_portfolio_summaries(self, tenant_id: str) -> list[PortfolioSummary]:
        with SessionLocal() as session:
            portfolio_rows = session.scalars(select(PortfolioTable).where(PortfolioTable.tenant_id == tenant_id).order_by(PortfolioTable.name)).all()
            scope_rows = session.scalars(select(PortfolioScopeTable).where(PortfolioScopeTable.tenant_id == tenant_id)).all()
            team_rows = session.scalars(select(TeamTable).where(TeamTable.tenant_id == tenant_id)).all()
            membership_rows = session.scalars(select(TeamMembershipTable).where(TeamMembershipTable.tenant_id == tenant_id)).all()
            request_rows = self._list_canonical_request_records(session, tenant_id=tenant_id)
            deployment_rows = session.scalars(select(DeploymentExecutionTable).where(DeploymentExecutionTable.tenant_id == tenant_id)).all()
        scopes_by_portfolio: dict[str, set[str]] = {}
        for scope in scope_rows:
            if scope.scope_type == "team":
                scopes_by_portfolio.setdefault(scope.portfolio_id, set()).add(scope.scope_key)
        team_ids = {row.id for row in team_rows}
        member_counts: dict[str, int] = {}
        for membership in membership_rows:
            member_counts[membership.team_id] = member_counts.get(membership.team_id, 0) + 1
        deployment_by_request = {row.request_id for row in deployment_rows if row.status == "succeeded"}
        summaries: list[PortfolioSummary] = []
        for portfolio in portfolio_rows:
            scoped_team_ids = scopes_by_portfolio.get(portfolio.id, set()) & team_ids
            scoped_requests = [row for row in request_rows if row.owner_team_id in scoped_team_ids]
            summaries.append(
                PortfolioSummary(
                    portfolio_id=portfolio.id,
                    portfolio_name=portfolio.name,
                    owner_team_id=portfolio.owner_team_id,
                    team_count=len(scoped_team_ids),
                    member_count=sum(member_counts.get(team_id, 0) for team_id in scoped_team_ids),
                    request_count=len(scoped_requests),
                    active_request_count=sum(
                        1 for row in scoped_requests if row.status in {
                            RequestStatus.SUBMITTED.value,
                            RequestStatus.VALIDATED.value,
                            RequestStatus.CLASSIFIED.value,
                            RequestStatus.OWNERSHIP_RESOLVED.value,
                            RequestStatus.PLANNED.value,
                            RequestStatus.QUEUED.value,
                            RequestStatus.IN_EXECUTION.value,
                            RequestStatus.AWAITING_REVIEW.value,
                            RequestStatus.UNDER_REVIEW.value,
                            RequestStatus.APPROVED.value,
                            RequestStatus.PROMOTION_PENDING.value,
                        }
                    ),
                    completed_request_count=sum(1 for row in scoped_requests if row.status == RequestStatus.COMPLETED.value),
                    deployment_count=sum(1 for row in scoped_requests if row.id in deployment_by_request),
                )
            )
        return summaries

    def list_delivery_dora(
        self,
        tenant_id: str,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryDoraRow]:
        with SessionLocal() as session:
            request_rows = self._list_canonical_request_records(session, tenant_id=tenant_id)
            deployment_rows = session.scalars(select(DeploymentExecutionTable).where(DeploymentExecutionTable.tenant_id == tenant_id)).all()
            signal_rows = session.scalars(select(RuntimeSignalTable).where(RuntimeSignalTable.tenant_id == tenant_id)).all()
            scope_rows = session.scalars(select(PortfolioScopeTable).where(PortfolioScopeTable.tenant_id == tenant_id)).all()
            portfolio_rows = {row.id: row for row in session.scalars(select(PortfolioTable).where(PortfolioTable.tenant_id == tenant_id)).all()}
        request_rows = self._filter_request_rows_for_analytics(request_rows, tenant_id, team_id, user_id, portfolio_id, scope_rows)

        request_ids_by_scope: dict[tuple[str, str], list] = {}
        if team_id:
            scoped_requests = [row for row in request_rows if row.owner_team_id == team_id]
            request_ids_by_scope[("team", team_id)] = scoped_requests
        elif user_id:
            scoped_requests = [row for row in request_rows if row.owner_user_id == user_id or row.submitter_id == user_id]
            request_ids_by_scope[("user", user_id)] = scoped_requests
        elif portfolio_id and portfolio_id in portfolio_rows:
            team_scopes = {row.scope_key for row in scope_rows if row.portfolio_id == portfolio_id and row.scope_type == "team"}
            scoped_requests = [row for row in request_rows if row.owner_team_id in team_scopes]
            request_ids_by_scope[("portfolio", portfolio_id)] = scoped_requests
        else:
            by_team: dict[str, list] = {}
            for row in request_rows:
                key = row.owner_team_id or "unassigned"
                by_team.setdefault(key, []).append(row)
            request_ids_by_scope = {("team", key): value for key, value in by_team.items()}

        restored_at_by_request: dict[str, datetime] = {}
        for signal in signal_rows:
            if signal.status == "completed":
                restored_at_by_request[signal.request_id] = self._as_utc(signal.received_at)

        rows: list[DeliveryDoraRow] = []
        for (scope_type, scope_key), scoped_requests in request_ids_by_scope.items():
            if not scoped_requests:
                continue
            deployed_requests = [row for row in scoped_requests if row.status in {RequestStatus.PROMOTED.value, RequestStatus.COMPLETED.value}]
            failures = [row for row in scoped_requests if row.status == RequestStatus.FAILED.value]
            lead_times = [
                max((self._as_utc(row.updated_at) - self._as_utc(row.created_at)).total_seconds() / 3600, 0.0)
                for row in deployed_requests
            ]
            mttrs = [
                max((restored_at_by_request[row.id] - self._as_utc(row.updated_at)).total_seconds() / 3600, 0.0)
                for row in failures
                if row.id in restored_at_by_request
            ]
            deployment_frequency = len([row for row in deployment_rows if row.request_id in {request.id for request in deployed_requests} and row.status == "succeeded"])
            rows.append(
                DeliveryDoraRow(
                    scope_type=scope_type,
                    scope_key=scope_key,
                    deployment_frequency=f"{deployment_frequency}/30d",
                    lead_time_hours=round(sum(lead_times) / len(lead_times), 2) if lead_times else 0.0,
                    change_failure_rate=f"{(len(failures) / max(len(deployed_requests), 1)) * 100:.1f}%",
                    mean_time_to_restore_hours=round(sum(mttrs) / len(mttrs), 2) if mttrs else 0.0,
                )
            )
        return sorted(rows, key=lambda row: (row.scope_type, row.scope_key))

    def list_delivery_lifecycle(
        self,
        tenant_id: str,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryLifecycleRow]:
        with SessionLocal() as session:
            request_rows = self._list_canonical_request_records(session, tenant_id=tenant_id)
            run_rows = session.scalars(select(RunTable)).all()
            review_rows = session.scalars(select(ReviewQueueTable)).all()
            promotion_rows = session.scalars(select(PromotionTable)).all()
            runtime_dispatch_rows = session.scalars(select(RuntimeDispatchTable).where(RuntimeDispatchTable.tenant_id == tenant_id)).all()
            scope_rows = session.scalars(select(PortfolioScopeTable).where(PortfolioScopeTable.tenant_id == tenant_id)).all()
            portfolio_rows = {row.id: row for row in session.scalars(select(PortfolioTable).where(PortfolioTable.tenant_id == tenant_id)).all()}

        request_rows = self._filter_request_rows_for_analytics(request_rows, tenant_id, team_id, user_id, portfolio_id, scope_rows)
        scoped_requests_by_scope = self._requests_by_scope(request_rows, scope_rows, portfolio_rows, portfolio_id, team_id, user_id)
        runs_by_request: dict[str, list] = {}
        for row in run_rows:
            runs_by_request.setdefault(row.request_id, []).append(row)
        reviews_by_request: dict[str, list] = {}
        for row in review_rows:
            reviews_by_request.setdefault(row.request_id, []).append(row)
        promotions_by_request: dict[str, list] = {}
        for row in promotion_rows:
            promotions_by_request.setdefault(row.request_id, []).append(row)
        dispatches_by_run: dict[str, list] = {}
        for row in runtime_dispatch_rows:
            dispatches_by_run.setdefault(row.run_id, []).append(row)

        rows: list[DeliveryLifecycleRow] = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        for (scope_type, scope_key), scoped_requests in scoped_requests_by_scope.items():
            if not scoped_requests:
                continue
            throughput = sum(1 for row in scoped_requests if self._as_utc(row.created_at) >= cutoff)
            lead_times: list[float] = []
            cycle_times: list[float] = []
            execution_times: list[float] = []
            queue_times: list[float] = []
            review_times: list[float] = []
            approval_times: list[float] = []
            promotion_times: list[float] = []

            for request_row in scoped_requests:
                if request_row.status in {RequestStatus.COMPLETED.value, RequestStatus.PROMOTED.value, RequestStatus.PROMOTION_PENDING.value, RequestStatus.APPROVED.value}:
                    lead_times.append(max((self._as_utc(request_row.updated_at) - self._as_utc(request_row.created_at)).total_seconds() / 3600, 0.0))
                if request_row.status not in {RequestStatus.DRAFT.value, RequestStatus.CANCELED.value, RequestStatus.VALIDATION_FAILED.value}:
                    cycle_times.append(max((self._as_utc(request_row.updated_at) - self._as_utc(request_row.created_at)).total_seconds() / 3600, 0.0))

                request_runs = runs_by_request.get(request_row.id, [])
                for run in request_runs:
                    elapsed_hours = self._parse_duration_to_hours(run.elapsed_time)
                    if elapsed_hours > 0:
                        execution_times.append(elapsed_hours)
                    run_dispatches = sorted(dispatches_by_run.get(run.id, []), key=lambda row: row.dispatched_at)
                    enqueue = next((row for row in run_dispatches if row.dispatch_type == "enqueue"), None)
                    start = next((row for row in run_dispatches if row.dispatch_type == "start"), None)
                    if enqueue and start:
                        queue_times.append(max((self._as_utc(start.dispatched_at) - self._as_utc(enqueue.dispatched_at)).total_seconds() / 3600, 0.0))

                request_reviews = reviews_by_request.get(request_row.id, [])
                if request_reviews:
                    review_times.append(float(len(request_reviews)) * 2.0)

                if request_row.status in {RequestStatus.APPROVED.value, RequestStatus.PROMOTION_PENDING.value, RequestStatus.PROMOTED.value, RequestStatus.COMPLETED.value}:
                    approval_times.append(1.0)

                request_promotions = promotions_by_request.get(request_row.id, [])
                for promotion in request_promotions:
                    history = promotion.promotion_history or []
                    if len(history) >= 2:
                        try:
                            first = datetime.fromisoformat(str(history[0]["timestamp"]).replace("Z", "+00:00"))
                            last = datetime.fromisoformat(str(history[-1]["timestamp"]).replace("Z", "+00:00"))
                            promotion_times.append(max((last - first).total_seconds() / 3600, 0.0))
                        except (KeyError, TypeError, ValueError):
                            promotion_times.append(0.0)

            rows.append(
                DeliveryLifecycleRow(
                    scope_type=scope_type,
                    scope_key=scope_key,
                    throughput_30d=throughput,
                    lead_time_hours=round(sum(lead_times) / len(lead_times), 2) if lead_times else 0.0,
                    cycle_time_hours=round(sum(cycle_times) / len(cycle_times), 2) if cycle_times else 0.0,
                    execution_time_hours=round(sum(execution_times) / len(execution_times), 2) if execution_times else 0.0,
                    queue_time_hours=round(sum(queue_times) / len(queue_times), 2) if queue_times else 0.0,
                    review_time_hours=round(sum(review_times) / len(review_times), 2) if review_times else 0.0,
                    approval_time_hours=round(sum(approval_times) / len(approval_times), 2) if approval_times else 0.0,
                    promotion_time_hours=round(sum(promotion_times) / len(promotion_times), 2) if promotion_times else 0.0,
                )
            )
        return sorted(rows, key=lambda row: (row.scope_type, row.scope_key))

    def list_delivery_trends(
        self,
        tenant_id: str,
        days: int = 30,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryTrendPoint]:
        with SessionLocal() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            request_rows = self._list_canonical_request_records(session, tenant_id=tenant_id, cutoff=cutoff)
            deployment_rows = session.scalars(select(DeploymentExecutionTable).where(DeploymentExecutionTable.tenant_id == tenant_id)).all()
            scope_rows = session.scalars(select(PortfolioScopeTable).where(PortfolioScopeTable.tenant_id == tenant_id)).all()
        request_rows = self._filter_request_rows_for_analytics(request_rows, tenant_id, team_id, user_id, portfolio_id, scope_rows)

        deployment_request_ids = {row.request_id for row in deployment_rows if row.status == "succeeded"}
        grouped: dict[str, dict[str, float]] = {}
        for row in request_rows:
            period_start = self._as_utc(row.updated_at).date().isoformat()
            bucket = grouped.setdefault(
                period_start,
                {"completed": 0.0, "failed": 0.0, "deployments": 0.0, "throughput": 0.0, "lead_time_hours": 0.0, "lead_time_count": 0.0},
            )
            bucket["throughput"] += 1
            bucket["completed"] += 1 if row.status in {RequestStatus.COMPLETED.value, RequestStatus.PROMOTED.value} else 0
            bucket["failed"] += 1 if row.status == RequestStatus.FAILED.value else 0
            bucket["deployments"] += 1 if row.id in deployment_request_ids else 0
            if row.status in {RequestStatus.COMPLETED.value, RequestStatus.PROMOTED.value, RequestStatus.PROMOTION_PENDING.value, RequestStatus.APPROVED.value}:
                bucket["lead_time_hours"] += max((self._as_utc(row.updated_at) - self._as_utc(row.created_at)).total_seconds() / 3600, 0.0)
                bucket["lead_time_count"] += 1

        rows: list[DeliveryTrendPoint] = []
        for period_start in sorted(grouped.keys()):
            bucket = grouped[period_start]
            lead_time_count = max(int(bucket["lead_time_count"]), 1)
            rows.append(
                DeliveryTrendPoint(
                    period_start=period_start,
                    completed_count=int(bucket["completed"]),
                    failed_count=int(bucket["failed"]),
                    deployment_count=int(bucket["deployments"]),
                    throughput_count=int(bucket["throughput"]),
                    lead_time_hours=round(bucket["lead_time_hours"] / lead_time_count, 2) if bucket["lead_time_count"] else 0.0,
                )
            )
        return rows

    def get_delivery_forecast(
        self,
        tenant_id: str,
        history_days: int = 30,
        forecast_days: int = 14,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> DeliveryForecastSummary:
        trend_rows = self.list_delivery_trends(tenant_id, history_days, portfolio_id, team_id, user_id)
        if not trend_rows:
            return DeliveryForecastSummary(
                forecast_days=forecast_days,
                avg_daily_throughput=0.0,
                avg_daily_deployments=0.0,
                projected_total_throughput=0.0,
                projected_total_deployments=0.0,
                projected_lead_time_hours=0.0,
            )

        avg_daily_throughput = sum(row.throughput_count for row in trend_rows) / len(trend_rows)
        avg_daily_deployments = sum(row.deployment_count for row in trend_rows) / len(trend_rows)
        projected_lead_time = sum(row.lead_time_hours for row in trend_rows) / len(trend_rows)
        return DeliveryForecastSummary(
            forecast_days=forecast_days,
            avg_daily_throughput=round(avg_daily_throughput, 2),
            avg_daily_deployments=round(avg_daily_deployments, 2),
            projected_total_throughput=round(avg_daily_throughput * forecast_days, 2),
            projected_total_deployments=round(avg_daily_deployments * forecast_days, 2),
            projected_lead_time_hours=round(projected_lead_time, 2),
        )

    def list_delivery_forecast_points(
        self,
        tenant_id: str,
        history_days: int = 30,
        forecast_days: int = 14,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryForecastPoint]:
        summary = self.get_delivery_forecast(tenant_id, history_days, forecast_days, portfolio_id, team_id, user_id)
        start = datetime.now(timezone.utc).date()
        return [
            DeliveryForecastPoint(
                period_start=(start + timedelta(days=offset + 1)).isoformat(),
                projected_throughput_count=summary.avg_daily_throughput,
                projected_deployment_count=summary.avg_daily_deployments,
                projected_lead_time_hours=summary.projected_lead_time_hours,
            )
            for offset in range(forecast_days)
        ]

    def get_performance_operations_summary(self, tenant_id: str) -> PerformanceOperationsSummary:
        now = datetime.now(timezone.utc)
        with SessionLocal() as session:
            requests = self._list_canonical_request_records(session, tenant_id=tenant_id)
            runtime_dispatches = session.scalars(select(RuntimeDispatchTable).where(RuntimeDispatchTable.tenant_id == tenant_id)).all()
            request_ids = {row.id for row in requests}
            promotions = session.scalars(select(PromotionTable)).all()
            promotions = [row for row in promotions if row.request_id in request_ids]
            promotion_ids = {row.id for row in promotions}
            check_runs = session.scalars(select(CheckRunTable)).all()
            reviews = session.scalars(select(ReviewQueueTable)).all()

        check_runs = [
            row for row in check_runs
            if (row.request_id and row.request_id in request_ids) or (row.promotion_id and row.promotion_id in promotion_ids)
        ]
        reviews = [row for row in reviews if row.request_id in request_ids]

        queued_checks = [row for row in check_runs if row.status == "queued"]
        running_checks = [row for row in check_runs if row.status == "running"]
        waiting_runs = [row for row in requests if row.status in {RequestStatus.QUEUED.value, RequestStatus.AWAITING_INPUT.value, RequestStatus.AWAITING_REVIEW.value}]
        failed_runs = [row for row in requests if row.status == RequestStatus.FAILED.value]
        stale_reviews = [row for row in reviews if row.stale]
        pending_promotions = [
            row for row in promotions
            if any(str(approval.get("state", "")).lower() == "pending" for approval in (row.required_approvals or []))
        ]

        check_queue_minutes = [max((now - row.queued_at).total_seconds() / 60, 0.0) for row in queued_checks]

        dispatches_by_run: dict[str, list] = {}
        for row in runtime_dispatches:
            dispatches_by_run.setdefault(row.run_id, []).append(row)
        runtime_queue_minutes: list[float] = []
        for rows in dispatches_by_run.values():
            ordered = sorted(rows, key=lambda row: row.dispatched_at)
            enqueue = next((row for row in ordered if row.dispatch_type == "enqueue"), None)
            start = next((row for row in ordered if row.dispatch_type == "start"), None)
            if enqueue and start:
                runtime_queue_minutes.append(max((self._as_utc(start.dispatched_at) - self._as_utc(enqueue.dispatched_at)).total_seconds() / 60, 0.0))

        return PerformanceOperationsSummary(
            queued_checks=len(queued_checks),
            running_checks=len(running_checks),
            waiting_runs=len(waiting_runs),
            failed_runs=len(failed_runs),
            stale_reviews=len(stale_reviews),
            pending_promotions=len(pending_promotions),
            avg_check_queue_minutes=round(sum(check_queue_minutes) / len(check_queue_minutes), 2) if check_queue_minutes else 0.0,
            avg_runtime_queue_minutes=round(sum(runtime_queue_minutes) / len(runtime_queue_minutes), 2) if runtime_queue_minutes else 0.0,
        )

    def list_performance_operations_trends(self, tenant_id: str, days: int = 30) -> list[PerformanceOperationsTrendPoint]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with SessionLocal() as session:
            requests = self._list_canonical_request_records(session, tenant_id=tenant_id, cutoff=cutoff)
            request_map = {row.id: row for row in requests}
            request_ids = {row.id for row in requests}
            promotions = session.scalars(select(PromotionTable)).all()
            promotions = [row for row in promotions if row.request_id in request_ids]
            promotion_ids = {row.id for row in promotions}
            check_runs = session.scalars(select(CheckRunTable).where(CheckRunTable.queued_at >= cutoff)).all()
            reviews = session.scalars(select(ReviewQueueTable)).all()

        check_runs = [
            row for row in check_runs
            if (row.request_id and row.request_id in request_ids) or (row.promotion_id and row.promotion_id in promotion_ids)
        ]
        reviews = [row for row in reviews if row.request_id in request_ids]

        grouped: dict[str, dict[str, int]] = {}

        def bucket(date_key: str) -> dict[str, int]:
            return grouped.setdefault(
                date_key,
                {
                    "queued_checks": 0,
                    "running_checks": 0,
                    "waiting_runs": 0,
                    "failed_runs": 0,
                    "stale_reviews": 0,
                    "pending_promotions": 0,
                },
            )

        for row in check_runs:
            current = bucket(self._as_utc(row.queued_at).date().isoformat())
            if row.status == "queued":
                current["queued_checks"] += 1
            if row.status == "running":
                current["running_checks"] += 1

        for row in requests:
            current = bucket(self._as_utc(row.updated_at).date().isoformat())
            if row.status in {RequestStatus.QUEUED.value, RequestStatus.AWAITING_INPUT.value, RequestStatus.AWAITING_REVIEW.value}:
                current["waiting_runs"] += 1
            if row.status == RequestStatus.FAILED.value:
                current["failed_runs"] += 1

        for row in reviews:
            request_row = request_map.get(row.request_id)
            if request_row is None:
                continue
            current = bucket(self._as_utc(request_row.updated_at).date().isoformat())
            if row.stale:
                current["stale_reviews"] += 1

        for row in promotions:
            history = row.promotion_history or []
            if not history:
                continue
            latest = None
            try:
                latest = datetime.fromisoformat(str(history[-1]["timestamp"]).replace("Z", "+00:00"))
            except (KeyError, TypeError, ValueError):
                latest = None
            if latest is None:
                continue
            if latest < cutoff:
                continue
            current = bucket(self._as_utc(latest).date().isoformat())
            if any(str(approval.get("state", "")).lower() == "pending" for approval in (row.required_approvals or [])):
                current["pending_promotions"] += 1

        return [
            PerformanceOperationsTrendPoint(
                period_start=period_start,
                queued_checks=values["queued_checks"],
                running_checks=values["running_checks"],
                waiting_runs=values["waiting_runs"],
                failed_runs=values["failed_runs"],
                stale_reviews=values["stale_reviews"],
                pending_promotions=values["pending_promotions"],
            )
            for period_start, values in sorted(grouped.items())
        ]

    def _requests_by_scope(self, request_rows, scope_rows, portfolio_rows, portfolio_id: str | None = None, team_id: str | None = None, user_id: str | None = None):
        if team_id:
            return {("team", team_id): [row for row in request_rows if row.owner_team_id == team_id]}
        if user_id:
            return {("user", user_id): [row for row in request_rows if row.owner_user_id == user_id or row.submitter_id == user_id]}
        if portfolio_id and portfolio_id in portfolio_rows:
            team_scopes = {row.scope_key for row in scope_rows if row.portfolio_id == portfolio_id and row.scope_type == "team"}
            return {("portfolio", portfolio_id): [row for row in request_rows if row.owner_team_id in team_scopes]}
        by_team: dict[str, list] = {}
        for row in request_rows:
            key = row.owner_team_id or "unassigned"
            by_team.setdefault(key, []).append(row)
        return {("team", key): value for key, value in by_team.items()}

    def _filter_request_rows_for_analytics(
        self,
        request_rows,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
        scope_rows=None,
    ):
        filtered = [row for row in request_rows if tenant_id is None or row.tenant_id == tenant_id]
        if portfolio_id and scope_rows is not None:
            portfolio_teams = {row.scope_key for row in scope_rows if row.portfolio_id == portfolio_id and row.scope_type == "team"}
            filtered = [row for row in filtered if row.owner_team_id in portfolio_teams]
        if team_id:
            filtered = [row for row in filtered if row.owner_team_id == team_id]
        if user_id:
            filtered = [row for row in filtered if row.owner_user_id == user_id or row.submitter_id == user_id]
        return filtered

    def _list_canonical_request_records(
        self,
        session,
        tenant_id: str | None = None,
        cutoff: datetime | None = None,
    ) -> list[RequestRecord]:
        query = select(RequestTable)
        if tenant_id is not None:
            query = query.where(RequestTable.tenant_id == tenant_id)
        if cutoff is not None:
            query = query.where(RequestTable.updated_at >= cutoff)
        sql_rows = session.scalars(query).all()
        records: dict[str, RequestRecord] = {
            row.id: self._request_from_row(row)
            for row in sql_rows
        }

        request_backend = (settings.request_persistence_backend or settings.persistence_backend or "sqlalchemy").lower()
        if request_backend != "dynamodb":
            return sorted(records.values(), key=lambda row: row.updated_at, reverse=True)

        from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

        dynamodb_adapter = DynamoDbGovernancePersistenceAdapter()
        for item in dynamodb_adapter._scan_items():
            if item.get("record_type") != "request":
                continue
            if tenant_id is not None and item.get("tenant_id") != tenant_id:
                continue
            request_id = item.get("id")
            if not request_id or request_id in records:
                continue
            record = dynamodb_adapter._request_item_to_record(item)
            if cutoff is not None and record.updated_at < cutoff:
                continue
            records[record.id] = record

        return sorted(records.values(), key=lambda row: row.updated_at, reverse=True)

    def _parse_duration_to_hours(self, duration: str) -> float:
        if not duration:
            return 0.0
        hours = 0.0
        hour_match = re.search(r"(\d+)h", duration)
        minute_match = re.search(r"(\d+)m", duration)
        if hour_match:
            hours += int(hour_match.group(1))
        if minute_match:
            hours += int(minute_match.group(1)) / 60
        return hours

    def list_event_ledger(
        self,
        page: int,
        page_size: int,
        tenant_id: str,
        request_id: str | None = None,
        run_id: str | None = None,
        artifact_id: str | None = None,
        promotion_id: str | None = None,
        check_run_id: str | None = None,
        event_type: str | None = None,
    ) -> PaginatedResponse[EventLedgerRecord]:
        with SessionLocal() as session:
            stmt = select(EventStoreTable).where(EventStoreTable.tenant_id == tenant_id)
            if request_id:
                stmt = stmt.where(EventStoreTable.request_id == request_id)
            if run_id:
                stmt = stmt.where(EventStoreTable.run_id == run_id)
            if artifact_id:
                stmt = stmt.where(EventStoreTable.artifact_id == artifact_id)
            if promotion_id:
                stmt = stmt.where(EventStoreTable.promotion_id == promotion_id)
            if check_run_id:
                stmt = stmt.where(EventStoreTable.check_run_id == check_run_id)
            if event_type:
                stmt = stmt.where(EventStoreTable.event_type == event_type)
            rows = session.scalars(stmt.order_by(desc(EventStoreTable.occurred_at), desc(EventStoreTable.id))).all()
        records = [self._event_ledger_record_from_row(row) for row in rows]
        if event_type in {None, "request.event_recorded"}:
            from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

            dynamodb_adapter = DynamoDbGovernancePersistenceAdapter()
            dynamo_items = [
                item
                for item in dynamodb_adapter._scan_items()
                if item.get("record_type") == "request_event" and item.get("tenant_id") == tenant_id
            ]
            if request_id:
                dynamo_items = [item for item in dynamo_items if item.get("request_id") == request_id]
            sql_request_event_keys = {
                (
                    row.request_id,
                    row.actor,
                    row.detail,
                    (row.payload or {}).get("reason_or_evidence"),
                )
                for row in rows
                if row.event_type == "request.event_recorded"
            }
            for item in dynamo_items:
                dedupe_key = (
                    item.get("request_id"),
                    item.get("actor"),
                    item.get("action"),
                    item.get("reason_or_evidence"),
                )
                if dedupe_key in sql_request_event_keys:
                    continue
                records.append(self._event_ledger_record_from_request_event_item(item))
        records = sorted(records, key=lambda row: row.occurred_at, reverse=True)
        return self._paginate(records, page, page_size)

    def list_event_outbox(
        self,
        page: int,
        page_size: int,
        tenant_id: str,
        request_id: str | None = None,
        status: str | None = None,
        topic: str | None = None,
    ) -> PaginatedResponse[EventOutboxRecord]:
        with SessionLocal() as session:
            stmt = select(EventOutboxTable).where(EventOutboxTable.tenant_id == tenant_id)
            if status:
                stmt = stmt.where(EventOutboxTable.status == status)
            if topic:
                stmt = stmt.where(EventOutboxTable.topic == topic)
            rows = session.scalars(stmt.order_by(desc(EventOutboxTable.created_at), desc(EventOutboxTable.id))).all()
        if request_id:
            rows = [row for row in rows if (row.payload or {}).get("request_id") == request_id]
        records = [self._event_outbox_record_from_row(row) for row in rows]
        return self._paginate(records, page, page_size)

    def create_request_draft(self, payload: CreateRequestDraft, actor_id: str = "user_demo", tenant_id: str = "tenant_demo") -> RequestRecord:
        with SessionLocal() as session:
            template_row = session.scalars(
                select(TemplateTable).where(
                    TemplateTable.id == payload.template_id,
                    TemplateTable.version == payload.template_version,
                    TemplateTable.tenant_id == tenant_id,
                )
            ).first()
            if template_row is None:
                raise ValueError(f"Template {payload.template_id}@{payload.template_version} is not available for tenant {tenant_id}")
            normalized_input_payload = self._validate_template_payload(
                template_row.template_schema,
                payload.input_payload,
                require_required=False,
            )
            next_id = self._next_request_id(session)
            now = datetime.now(timezone.utc)
            row = RequestTable(
                id=next_id,
                tenant_id=tenant_id,
                request_type="custom",
                template_id=payload.template_id,
                template_version=payload.template_version,
                title=payload.title,
                summary=payload.summary,
                status="draft",
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
            session.add(row)
            self._append_event(
                session=session,
                request_id=next_id,
                actor=actor_id,
                action="Draft Created",
                reason_or_evidence="Initial draft created through API",
            )
            session.commit()
            session.refresh(row)
        return self._request_from_row(row)

    def submit_request(self, request_id: str, payload: SubmitRequest, tenant_id: str | None = None) -> RequestRecord:
        with SessionLocal() as session:
            row = session.get(RequestTable, request_id)
            if row is None:
                if tenant_id is None:
                    raise StopIteration(request_id)
                from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

                return DynamoDbGovernancePersistenceAdapter().submit_request(request_id, payload, tenant_id)
            self._ensure_request_tenant_access(row, tenant_id)
            template_row = session.scalars(
                select(TemplateTable).where(
                    TemplateTable.id == row.template_id,
                    TemplateTable.version == row.template_version,
                    TemplateTable.tenant_id == row.tenant_id,
                )
            ).first()
            if template_row is None:
                raise ValueError(f"Bound template {row.template_id}@{row.template_version} is no longer available")
            row.input_payload = self._validate_template_payload(
                template_row.template_schema,
                row.input_payload or {},
                require_required=True,
            )
            routing = self._resolve_request_routing(template_row.template_schema, row.input_payload or {})
            row.owner_team_id = routing["owner_team_id"] or row.owner_team_id
            row.workflow_binding_id = routing["workflow_binding_id"] or row.workflow_binding_id
            row.policy_context = {
                **dict(row.policy_context or {}),
                "routing": {
                    "resolved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "owner_team_id": row.owner_team_id,
                    "workflow_binding_id": row.workflow_binding_id,
                    "reviewers": routing["reviewers"],
                    "promotion_approvers": routing["promotion_approvers"],
                },
            }
            current_status = RequestStatus(row.status)
            if current_status not in self.SUBMITTABLE_STATUSES:
                raise ValueError(f"Request {request_id} cannot be submitted from status {row.status}")
            row.status = RequestStatus.SUBMITTED.value
            row.updated_at = datetime.now(timezone.utc)
            row.updated_by = payload.actor_id
            row.version += 1
            check_dispatch_service.enqueue_request_checks(session, request_id, payload.actor_id, payload.reason)
            self._append_event(
                session=session,
                request_id=request_id,
                actor=payload.actor_id,
                action="Submitted",
                reason_or_evidence=payload.reason,
            )
            self._append_event(
                session=session,
                request_id=request_id,
                actor=payload.actor_id,
                action="Routing Resolved",
                reason_or_evidence=f"owner_team={row.owner_team_id or 'unassigned'} workflow_binding={row.workflow_binding_id or 'unassigned'} reviewers={', '.join(routing['reviewers']) or 'none'}",
            )
            session.commit()
            session.refresh(row)
        return self._request_from_row(row)

    def amend_request(self, request_id: str, payload: AmendRequest, tenant_id: str | None = None) -> RequestRecord:
        with SessionLocal() as session:
            row = session.get(RequestTable, request_id)
            if row is None:
                if tenant_id is None:
                    raise StopIteration(request_id)
                from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

                return DynamoDbGovernancePersistenceAdapter().amend_request(request_id, payload, tenant_id)
            self._ensure_request_tenant_access(row, tenant_id)
            current_status = RequestStatus(row.status)
            if current_status not in self.AMENDABLE_STATUSES:
                raise ValueError(f"Request {request_id} cannot be amended from status {row.status}")
            if payload.title is not None:
                row.title = payload.title
            if payload.summary is not None:
                row.summary = payload.summary
            if payload.priority is not None:
                row.priority = payload.priority.value
            if payload.input_payload is not None:
                row.input_payload = payload.input_payload
            row.status = RequestStatus.DRAFT.value
            row.updated_at = datetime.now(timezone.utc)
            row.updated_by = payload.actor_id
            row.version += 1
            self._append_event(
                session=session,
                request_id=request_id,
                actor=payload.actor_id,
                action="Amended",
                reason_or_evidence=payload.reason,
            )
            session.commit()
            session.refresh(row)
        return self._request_from_row(row)

    def cancel_request(self, request_id: str, payload: CancelRequest, tenant_id: str | None = None) -> RequestRecord:
        with SessionLocal() as session:
            row = session.get(RequestTable, request_id)
            if row is None:
                if tenant_id is None:
                    raise StopIteration(request_id)
                from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

                return DynamoDbGovernancePersistenceAdapter().cancel_request(request_id, payload, tenant_id)
            self._ensure_request_tenant_access(row, tenant_id)
            current_status = RequestStatus(row.status)
            if current_status not in self.CANCELABLE_STATUSES:
                raise ValueError(f"Request {request_id} cannot be canceled from status {row.status}")
            row.status = RequestStatus.CANCELED.value
            row.updated_at = datetime.now(timezone.utc)
            row.updated_by = payload.actor_id
            row.version += 1
            self._append_event(
                session=session,
                request_id=request_id,
                actor=payload.actor_id,
                action="Canceled",
                reason_or_evidence=payload.reason,
            )
            session.commit()
            session.refresh(row)
        return self._request_from_row(row)

    def transition_request(self, request_id: str, payload: TransitionRequest, tenant_id: str | None = None) -> RequestRecord:
        with SessionLocal() as session:
            row = session.get(RequestTable, request_id)
            if row is None:
                if tenant_id is None:
                    raise StopIteration(request_id)
                from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

                return DynamoDbGovernancePersistenceAdapter().transition_request(request_id, payload, tenant_id)
            self._ensure_request_tenant_access(row, tenant_id)
            current_status = RequestStatus(row.status)
            target_status = payload.target_status
            if target_status in {RequestStatus.DRAFT, RequestStatus.SUBMITTED, RequestStatus.CANCELED, RequestStatus.ARCHIVED}:
                raise ValueError(f"Use the dedicated mutation for target status {target_status.value}")
            allowed_targets = self.TRANSITION_RULES.get(current_status, set())
            if target_status not in allowed_targets:
                raise ValueError(f"Request {request_id} cannot transition from {row.status} to {target_status.value}")
            required_checks = policy_check_service.active_transition_gate_check_names(session, target_status, row.tenant_id)
            if required_checks:
                if check_dispatch_service.has_pending_request_check_run(session, row.id):
                    raise ValueError(f"Request checks are still queued or running for {request_id}. Retry the transition after they complete")
                try:
                    policy_check_service.assert_request_transition_ready(session, row.id, target_status, row.tenant_id)
                except ValueError as exc:
                    check_dispatch_service.enqueue_request_checks(
                        session,
                        request_id,
                        payload.actor_id,
                        f"Transition preflight for {target_status.value}",
                    )
                    session.commit()
                    raise ValueError(f"{exc}. Automated evaluation queued") from exc
            row.status = target_status.value
            row.updated_at = datetime.now(timezone.utc)
            row.updated_by = payload.actor_id
            row.version += 1
            self._apply_transition_side_effects(session, row, current_status, target_status, payload.actor_id)
            self._append_event(
                session=session,
                request_id=request_id,
                actor=payload.actor_id,
                action=f"Transitioned to {target_status.value}",
                reason_or_evidence=payload.reason,
            )
            session.commit()
            session.refresh(row)
        return self._request_from_row(row)

    def decide_instructional_workflow_stage(
        self,
        request_id: str,
        payload: InstructionalWorkflowDecisionRequest,
        tenant_id: str,
    ) -> InstructionalWorkflowProjectionRecord:
        with SessionLocal() as session:
            row = session.get(RequestTable, request_id)
            if row is None:
                raise StopIteration(request_id)
            self._ensure_request_tenant_access(row, tenant_id)
            if not self._is_instructional_template(row.template_id):
                raise ValueError(f"Request {request_id} is not an instructional governance request")
            if row.status in {RequestStatus.CANCELED.value, RequestStatus.ARCHIVED.value, RequestStatus.COMPLETED.value}:
                raise ValueError(f"Request {request_id} cannot accept instructional stage decisions from status {row.status}")

            projection = self._build_instructional_projection_from_row(row, self.list_audit_entries(request_id, row.tenant_id))
            if projection.current_stage_id is None:
                raise ValueError(f"Request {request_id} does not have an active instructional review stage")
            if projection.current_stage_id != payload.stage_id:
                raise ValueError(
                    f"Instructional stage decision must target the active stage {projection.current_stage_id.value}, not {payload.stage_id.value}"
                )

            current_status = RequestStatus(row.status)
            stage_ids = self._instructional_stage_ids(row.template_id)
            current_index = stage_ids.index(payload.stage_id)
            is_final_stage = current_index == len(stage_ids) - 1

            if payload.decision == InstructionalWorkflowDecision.REQUEST_CHANGES:
                row.status = RequestStatus.CHANGES_REQUESTED.value
                row.updated_at = datetime.now(timezone.utc)
                row.updated_by = payload.actor_id
                row.version += 1
                self._append_event(
                    session=session,
                    request_id=request_id,
                    actor=payload.actor_id,
                    action=f"Instructional Stage Changes Requested: {payload.stage_id.value}",
                    reason_or_evidence=payload.notes or "Instructional review requested changes",
                )
                if current_status != RequestStatus.CHANGES_REQUESTED:
                    self._apply_transition_side_effects(session, row, current_status, RequestStatus.CHANGES_REQUESTED, payload.actor_id)
                    self._append_event(
                        session=session,
                        request_id=request_id,
                        actor=payload.actor_id,
                        action=f"Transitioned to {RequestStatus.CHANGES_REQUESTED.value}",
                        reason_or_evidence=payload.notes or "Instructional stage decision requested changes",
                    )
            else:
                target_status = RequestStatus.APPROVED if is_final_stage else RequestStatus.UNDER_REVIEW
                row.status = target_status.value
                row.updated_at = datetime.now(timezone.utc)
                row.updated_by = payload.actor_id
                row.version += 1
                self._append_event(
                    session=session,
                    request_id=request_id,
                    actor=payload.actor_id,
                    action=f"Instructional Stage Approved: {payload.stage_id.value}",
                    reason_or_evidence=payload.notes or "Instructional review stage approved",
                )
                if current_status != target_status:
                    self._apply_transition_side_effects(session, row, current_status, target_status, payload.actor_id)
                    self._append_event(
                        session=session,
                        request_id=request_id,
                        actor=payload.actor_id,
                        action=f"Transitioned to {target_status.value}",
                        reason_or_evidence=payload.notes or "Instructional stage decision recorded",
                    )

            session.commit()
            session.refresh(row)

        return self._build_instructional_projection_from_row(row, self.list_audit_entries(request_id, row.tenant_id))

    def clone_request(self, request_id: str, payload: CloneRequest, tenant_id: str | None = None) -> RequestRecord:
        with SessionLocal() as session:
            source_row = session.get(RequestTable, request_id)
            if source_row is None:
                if tenant_id is None:
                    raise StopIteration(request_id)
                from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

                return DynamoDbGovernancePersistenceAdapter().clone_request(request_id, payload, tenant_id)
            self._ensure_request_tenant_access(source_row, tenant_id)
            now = datetime.now(timezone.utc)
            next_id = self._next_request_id(session)
            cloned_row = RequestTable(
                id=next_id,
                tenant_id=source_row.tenant_id,
                request_type=source_row.request_type,
                template_id=source_row.template_id,
                template_version=source_row.template_version,
                title=payload.title or f"{source_row.title} (Clone)",
                summary=payload.summary or source_row.summary,
                status=RequestStatus.DRAFT.value,
                priority=source_row.priority,
                sla_policy_id=source_row.sla_policy_id,
                submitter_id=payload.actor_id,
                owner_team_id=source_row.owner_team_id,
                owner_user_id=source_row.owner_user_id,
                workflow_binding_id=source_row.workflow_binding_id,
                current_run_id=None,
                policy_context=source_row.policy_context,
                input_payload=source_row.input_payload,
                tags=source_row.tags,
                created_at=now,
                created_by=payload.actor_id,
                updated_at=now,
                updated_by=payload.actor_id,
                version=1,
                is_archived=False,
            )
            session.add(cloned_row)
            self._append_event(
                session=session,
                request_id=request_id,
                actor=payload.actor_id,
                action="Cloned",
                reason_or_evidence=f"{payload.reason}. Replacement draft: {next_id}",
            )
            self._append_relationship(
                session=session,
                source_request_id=request_id,
                target_request_id=next_id,
                relationship_type="clone",
                actor_id=payload.actor_id,
            )
            self._append_event(
                session=session,
                request_id=next_id,
                actor=payload.actor_id,
                action="Draft Created",
                reason_or_evidence=f"Cloned from request {request_id}",
            )
            session.commit()
            session.refresh(cloned_row)
        return self._request_from_row(cloned_row)

    def supersede_request(self, request_id: str, payload: SupersedeRequest, tenant_id: str | None = None) -> RequestRecord:
        with SessionLocal() as session:
            row = session.get(RequestTable, request_id)
            replacement_row = session.get(RequestTable, payload.replacement_request_id)
            if row is None or replacement_row is None:
                if tenant_id is None:
                    missing_id = request_id if row is None else payload.replacement_request_id
                    raise StopIteration(missing_id)
                from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

                return DynamoDbGovernancePersistenceAdapter().supersede_request(request_id, payload, tenant_id)
            self._ensure_request_tenant_access(row, tenant_id)
            self._ensure_request_tenant_access(replacement_row, tenant_id)
            if replacement_row.id == row.id:
                raise ValueError("Replacement request must differ from the request being superseded")
            if row.status in {RequestStatus.ARCHIVED.value, RequestStatus.CANCELED.value, RequestStatus.COMPLETED.value}:
                raise ValueError(f"Request {request_id} cannot be superseded from status {row.status}")
            row.status = RequestStatus.ARCHIVED.value
            row.is_archived = True
            row.updated_at = datetime.now(timezone.utc)
            row.updated_by = payload.actor_id
            row.version += 1
            self._append_event(
                session=session,
                request_id=request_id,
                actor=payload.actor_id,
                action="Superseded",
                reason_or_evidence=f"{payload.reason}. Replacement request: {payload.replacement_request_id}",
            )
            self._append_relationship(
                session=session,
                source_request_id=request_id,
                target_request_id=payload.replacement_request_id,
                relationship_type="supersedes",
                actor_id=payload.actor_id,
            )
            self._append_event(
                session=session,
                request_id=payload.replacement_request_id,
                actor=payload.actor_id,
                action="Superseding Request Linked",
                reason_or_evidence=f"Supersedes request {request_id}",
            )
            session.commit()
            session.refresh(row)
        return self._request_from_row(row)

    @staticmethod
    def _request_from_row(row: RequestTable, projection_rows: list[ProjectionMappingTable] | None = None) -> RequestRecord:
        sla_risk_level, sla_risk_reason = GovernanceRepository._compute_sla_risk(row)
        projection_records = []
        for projection_row in projection_rows or []:
            record = projection_service._record_from_row(projection_row)
            record.conflicts = projection_service.detect_conflicts(record.id)
            projection_records.append(record)
        return RequestRecord.model_validate(
            {
                "id": row.id,
                "tenant_id": row.tenant_id,
                "request_type": row.request_type,
                "template_id": row.template_id,
                "template_version": row.template_version,
                "title": row.title,
                "summary": row.summary,
                "status": row.status,
                "priority": row.priority,
                "sla_policy_id": row.sla_policy_id,
                "submitter_id": row.submitter_id,
                "owner_team_id": row.owner_team_id,
                "owner_user_id": row.owner_user_id,
                "workflow_binding_id": row.workflow_binding_id,
                "current_run_id": row.current_run_id,
                "policy_context": row.policy_context,
                "input_payload": row.input_payload,
                "tags": row.tags,
                "created_at": row.created_at,
                "created_by": row.created_by,
                "updated_at": row.updated_at,
                "updated_by": row.updated_by,
                "version": row.version,
                "is_archived": row.is_archived,
                "sla_risk_level": sla_risk_level,
                "sla_risk_reason": sla_risk_reason,
                "federated_projection_count": len(projection_records),
                "federated_conflict_count": sum(len(record.conflicts) for record in projection_records),
            }
        )

    @classmethod
    def _compute_sla_risk(cls, row: RequestTable) -> tuple[str | None, str | None]:
        return _sm_compute_sla_risk(row.status, row.priority, row.sla_policy_id, row.updated_at)

    @staticmethod
    def _ensure_request_tenant_access(row: RequestTable | None, tenant_id: str | None) -> None:
        if row is None:
            raise StopIteration
        if tenant_id and row.tenant_id != tenant_id:
            raise PermissionError(f"Tenant {tenant_id} cannot access request {row.id}")

    @staticmethod
    def _template_from_row(row: TemplateTable) -> TemplateRecord:
        return TemplateRecord.model_validate(
            {
                "id": row.id,
                "version": row.version,
                "name": row.name,
                "description": row.description,
                "status": row.status,
                "schema": row.template_schema,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
        )

    # Delegated to app.domain.template_engine
    _coerce_template_value = staticmethod(_te.coerce_value)
    _conditional_rule_matches = staticmethod(_te.conditional_rule_matches)

    def _validate_template_payload(self, template_schema: dict, payload: dict, *, require_required: bool) -> dict:
        return _te.validate_payload(template_schema, payload, require_required=require_required)

    def _validate_template_definition(self, template_schema: dict) -> TemplateValidationResult:
        return _te.validate_definition(template_schema)

    # Delegated to app.domain.template_engine
    _resolve_routing_value = staticmethod(_te.resolve_routing_value)

    def _resolve_request_routing(self, template_schema: dict, input_payload: dict) -> dict:
        return _te.resolve_routing(template_schema, input_payload)

    @staticmethod
    def _run_detail_from_row(
        row: RunTable,
        dispatch_rows: list[RuntimeDispatchTable] | None = None,
        signal_rows: list[RuntimeSignalTable] | None = None,
        projection_rows: list[ProjectionMappingTable] | None = None,
    ) -> RunDetail:
        projection_records = []
        for projection in projection_rows or []:
            record = projection_service._record_from_row(projection)
            record.conflicts = projection_service.detect_conflicts(record.id)
            projection_records.append(record)
        return RunDetail.model_validate(
            {
                "id": row.id,
                "request_id": row.request_id,
                "workflow": row.workflow,
                "status": row.status,
                "current_step": row.current_step,
                "elapsed_time": row.elapsed_time,
                "waiting_reason": row.waiting_reason,
                "updated_at": row.updated_at.isoformat().replace("+00:00", "Z"),
                "owner_team": row.owner_team,
                "federated_projection_count": len(projection_records),
                "federated_conflict_count": sum(len(record.conflicts) for record in projection_records),
                "workflow_identity": row.workflow_identity,
                "progress_percent": row.progress_percent,
                "current_step_input_summary": row.current_step_input_summary,
                "current_step_output_summary": row.current_step_output_summary,
                "failure_reason": row.failure_reason,
                "command_surface": row.command_surface,
                "steps": row.steps,
                "run_context": row.run_context,
                "conversation_thread_id": row.conversation_thread_id,
                "runtime_dispatches": [
                    {
                        "id": dispatch.id,
                        "run_id": dispatch.run_id,
                        "request_id": dispatch.request_id,
                        "integration_id": dispatch.integration_id,
                        "dispatch_type": dispatch.dispatch_type,
                        "status": dispatch.status,
                        "external_reference": dispatch.external_reference,
                        "detail": dispatch.detail,
                        "payload": dispatch.payload,
                        "response_payload": dispatch.response_payload,
                        "dispatched_at": dispatch.dispatched_at.isoformat().replace("+00:00", "Z"),
                    }
                    for dispatch in (dispatch_rows or [])
                ],
                "runtime_signals": [
                    {
                        "event_id": signal.event_id,
                        "source": signal.source,
                        "status": signal.status,
                        "current_step": signal.current_step,
                        "detail": signal.detail,
                        "payload": signal.payload,
                        "received_at": signal.received_at.isoformat().replace("+00:00", "Z"),
                    }
                    for signal in (signal_rows or [])
                ],
                "federated_projections": projection_records,
            }
        )

    @staticmethod
    def _get_request_row(session, request_id: str) -> RequestTable:
        row = session.get(RequestTable, request_id)
        if row is None:
            raise StopIteration(request_id)
        return row

    def _get_request_record(self, session, request_id: str, tenant_id: str | None) -> RequestRecord:
        request = get_request_state(request_id, tenant_id)
        if request is not None:
            return request
        row = session.get(RequestTable, request_id)
        if row is None:
            raise StopIteration(request_id)
        self._ensure_request_tenant_access(row, tenant_id)
        return self._request_from_row(row)

    def _ensure_request_access(self, session, request_id: str, tenant_id: str | None) -> RequestTable:
        row = self._get_request_row(session, request_id)
        self._ensure_request_tenant_access(row, tenant_id)
        return row

    def _append_event(self, session, request_id: str, actor: str, action: str, reason_or_evidence: str) -> None:
        request_row = session.get(RequestTable, request_id)
        if request_row is None:
            request_row = next(
                (
                    candidate
                    for candidate in session.new
                    if isinstance(candidate, RequestTable) and candidate.id == request_id
                ),
                None,
            )
        if request_row is None:
            raise StopIteration(request_id)
        session.add(
            RequestEventTable(
                request_id=request_id,
                timestamp=datetime.now(timezone.utc),
                actor=actor,
                action=action,
                object_type="request",
                object_id=request_id,
                reason_or_evidence=reason_or_evidence,
            )
        )
        event_store_service.append(
            session,
            tenant_id=request_row.tenant_id,
            event_type="request.event_recorded",
            aggregate_type="request",
            aggregate_id=request_id,
            request_id=request_id,
            actor=actor,
            detail=action,
            payload={"reason_or_evidence": reason_or_evidence, "status": request_row.status},
        )

    @staticmethod
    def _next_request_id(session) -> str:
        return f"req_{uuid4().hex[:12]}"

    @staticmethod
    def _next_run_id(session) -> str:
        return f"run_{uuid4().hex[:12]}"

    @staticmethod
    def _next_review_queue_id(session) -> str:
        return f"revq_{uuid4().hex[:12]}"

    @staticmethod
    def _next_promotion_id(session) -> str:
        return f"pro_{uuid4().hex[:12]}"

    @staticmethod
    def _next_check_result_id(session) -> str:
        return f"chk_{uuid4().hex[:12]}"

    @staticmethod
    def _next_check_override_id(session) -> str:
        return f"ovr_{uuid4().hex[:12]}"

    @staticmethod
    def _next_artifact_id(session) -> str:
        return f"art_{uuid4().hex[:12]}"

    @staticmethod
    def _next_artifact_version_id(session) -> str:
        return f"artv_{uuid4().hex[:12]}"

    @staticmethod
    def _next_deployment_execution_id(session) -> str:
        return f"dep_{uuid4().hex[:12]}"

    @staticmethod
    def _next_runtime_dispatch_id(session) -> str:
        return f"rtd_{uuid4().hex[:12]}"

    @staticmethod
    def _append_relationship(
        session,
        source_request_id: str,
        target_request_id: str,
        relationship_type: str,
        actor_id: str,
    ) -> None:
        session.add(
            RequestRelationshipTable(
                source_request_id=source_request_id,
                target_request_id=target_request_id,
                relationship_type=relationship_type,
                created_at=datetime.now(timezone.utc),
                created_by=actor_id,
            )
        )

    @staticmethod
    def _relationship_from_predecessor_row(row: RequestRelationshipTable) -> RequestRelationship:
        return RequestRelationship(request_id=row.source_request_id, relationship_type=row.relationship_type)

    @staticmethod
    def _relationship_from_successor_row(row: RequestRelationshipTable) -> RequestRelationship:
        return RequestRelationship(request_id=row.target_request_id, relationship_type=row.relationship_type)

    @staticmethod
    def _review_queue_item_from_row(row: ReviewQueueTable, request_row: RequestTable | RequestRecord | None) -> ReviewQueueItem:
        blocking_status = row.blocking_status
        if not blocking_status and request_row is not None:
            request_status = request_row.status.value if hasattr(request_row.status, "value") else str(request_row.status)
            if request_status in {
                RequestStatus.APPROVED.value,
                RequestStatus.PROMOTION_PENDING.value,
                RequestStatus.PROMOTED.value,
                RequestStatus.COMPLETED.value,
            }:
                blocking_status = "Approved"
        return ReviewQueueItem.model_validate(
            {
                "id": row.id,
                "request_id": row.request_id,
                "review_scope": row.review_scope,
                "artifact_or_changeset": row.artifact_or_changeset,
                "type": row.type,
                "priority": row.priority,
                "sla": row.sla,
                "blocking_status": blocking_status,
                "assigned_reviewer": row.assigned_reviewer,
                "stale": row.stale,
            }
        )

    def _apply_transition_side_effects(
        self,
        session,
        row: RequestTable,
        current_status: RequestStatus,
        target_status: RequestStatus,
        actor_id: str,
    ) -> None:
        if target_status in {RequestStatus.PLANNED, RequestStatus.QUEUED, RequestStatus.IN_EXECUTION, RequestStatus.AWAITING_REVIEW}:
            self._ensure_run_for_request(session, row, target_status)

        if target_status == RequestStatus.QUEUED:
            row.workflow_binding_id = row.workflow_binding_id or f"wf_{row.template_id}_{row.template_version.replace('.', '_')}"
            if row.current_run_id:
                self._dispatch_run_to_runtime(session, row, row.current_run_id, "enqueue", actor_id)

        if target_status == RequestStatus.IN_EXECUTION and row.current_run_id:
            self._ensure_artifact_for_request(session, row, actor_id, artifact_status="in_revision", review_state="pending", append_version=True)
            run_row = session.get(RunTable, row.current_run_id)
            if run_row is not None:
                run_row.status = RunStatus.RUNNING.value
                run_row.current_step = "Execute Governed Workflow"
                run_row.waiting_reason = None
                run_row.progress_percent = max(run_row.progress_percent, 35)
                run_row.current_step_input_summary = "Request entered governed execution."
                run_row.current_step_output_summary = "Execution in progress."
                run_row.updated_at = datetime.now(timezone.utc)
            self._dispatch_run_to_runtime(session, row, row.current_run_id, "start", actor_id)

        if target_status == RequestStatus.AWAITING_REVIEW:
            artifact_row = self._ensure_artifact_for_request(session, row, actor_id, artifact_status="awaiting_review", review_state="pending", append_version=True)
            self._ensure_review_queue_item(session, row)
            check_dispatch_service.enqueue_request_checks(session, row.id, actor_id, "Review-entry request checks queued")
            review_row = session.scalars(select(ReviewQueueTable).where(ReviewQueueTable.request_id == row.id)).first()
            if review_row is not None:
                review_row.artifact_or_changeset = f"{artifact_row.name} {artifact_row.current_version}"
            if row.current_run_id:
                run_row = session.get(RunTable, row.current_run_id)
                if run_row is not None:
                    run_row.status = RunStatus.WAITING.value
                    run_row.current_step = "Human Review"
                    run_row.waiting_reason = "Awaiting reviewer approval"
                    run_row.progress_percent = max(run_row.progress_percent, 75)
                    run_row.updated_at = datetime.now(timezone.utc)

        if target_status == RequestStatus.UNDER_REVIEW:
            self._update_artifact_review_state(session, row.id, artifact_status="under_review", review_state="pending", stale_review=False)
            self._update_review_queue_status(session, row.id, "Review in progress")

        if target_status == RequestStatus.CHANGES_REQUESTED:
            self._update_artifact_review_state(session, row.id, artifact_status="changes_requested", review_state="changes_requested", stale_review=True)
            self._update_review_queue_status(session, row.id, "Changes requested")

        if target_status == RequestStatus.APPROVED:
            self._update_artifact_review_state(session, row.id, artifact_status="approved", review_state="approved", stale_review=False)
            self._update_review_queue_status(session, row.id, "Approved")
            check_dispatch_service.enqueue_request_checks(session, row.id, actor_id, "Approval request checks queued")
            self._apply_registration_request_side_effects(session, row, actor_id, target_status)
            if row.current_run_id:
                run_row = session.get(RunTable, row.current_run_id)
                if run_row is not None:
                    run_row.status = RunStatus.COMPLETED.value
                    run_row.current_step = "Review Approved"
                    run_row.waiting_reason = None
                    run_row.progress_percent = 100
                    run_row.current_step_output_summary = "Review approved and ready for promotion or completion."
                    run_row.updated_at = datetime.now(timezone.utc)

        if target_status == RequestStatus.PROMOTION_PENDING:
            self._update_artifact_review_state(session, row.id, artifact_status="promotion_pending", review_state="approved", stale_review=False, promotion_relevant=True)
            self._ensure_promotion_record(session, row, actor_id)
            promotion_row = session.scalars(select(PromotionTable).where(PromotionTable.request_id == row.id)).first()
            if promotion_row is not None:
                check_dispatch_service.enqueue_promotion_checks(session, promotion_row.id, row.id, actor_id, "Promotion gate checks queued")

        if target_status == RequestStatus.PROMOTED:
            self._update_artifact_review_state(session, row.id, artifact_status="promoted", review_state="approved", stale_review=False, promotion_relevant=True)
            promotion_row = session.scalars(select(PromotionTable).where(PromotionTable.request_id == row.id)).first()
            if promotion_row is not None:
                promotion_row.execution_readiness = "Promotion executed successfully."
                promotion_history = list(promotion_row.promotion_history)
                promotion_history.append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "actor": actor_id,
                        "action": "Promotion executed",
                    }
                )
                promotion_row.promotion_history = promotion_history

        if target_status == RequestStatus.COMPLETED and row.current_run_id:
            self._update_artifact_review_state(session, row.id, artifact_status="completed", review_state="approved", stale_review=False, promotion_relevant=True)
            self._apply_registration_request_side_effects(session, row, actor_id, target_status)
            run_row = session.get(RunTable, row.current_run_id)
            if run_row is not None:
                run_row.status = RunStatus.COMPLETED.value
                run_row.current_step = "Completed"
                run_row.waiting_reason = None
                run_row.progress_percent = 100
                run_row.updated_at = datetime.now(timezone.utc)

    def _apply_registration_request_side_effects(
        self,
        session,
        row: RequestTable,
        actor_id: str,
        target_status: RequestStatus,
    ) -> None:
        if row.template_id != "tmpl_user_registration":
            return
        payload = dict(row.input_payload or {})
        email = str(payload.get("email") or "").strip().lower()
        if not email:
            return
        existing = session.scalars(
            select(UserTable).where(
                UserTable.tenant_id == row.tenant_id,
                func.lower(UserTable.email) == email,
            )
        ).first()
        requested_roles = payload.get("requested_roles") or []
        if isinstance(requested_roles, str):
            requested_roles = [requested_roles]
        normalized_roles = [role for role in requested_roles if role in {item.value for item in PrincipalRole}]
        requested_team_id = str(payload.get("requested_team_id") or "").strip()
        requested_team = None
        if requested_team_id:
            requested_team = session.get(TeamTable, requested_team_id)
            if requested_team is None or requested_team.tenant_id != row.tenant_id or requested_team.status != "active":
                requested_team = None
        now = datetime.now(timezone.utc)
        target_account_status = "active" if target_status == RequestStatus.COMPLETED and existing and existing.password_hash and not existing.password_reset_required else "pending_activation"
        if existing is None:
            user_id = f"user_{uuid4().hex[:10]}"
            created_user = UserTable(
                id=user_id,
                tenant_id=row.tenant_id,
                display_name=str(payload.get("display_name") or payload.get("email") or "Pending User"),
                email=email,
                role_summary=normalized_roles or ["submitter"],
                status=target_account_status,
                password_hash=None,
                password_reset_required=True,
                registration_request_id=row.id,
                created_at=now,
                updated_at=now,
            )
            session.add(created_user)
            if requested_team is not None:
                membership = session.scalars(
                    select(TeamMembershipTable).where(
                        TeamMembershipTable.tenant_id == row.tenant_id,
                        TeamMembershipTable.team_id == requested_team.id,
                        TeamMembershipTable.user_id == created_user.id,
                    )
                ).first()
                if membership is None:
                    session.add(
                        TeamMembershipTable(
                            id=f"tm_{requested_team.id}_{created_user.id}",
                            tenant_id=row.tenant_id,
                            team_id=requested_team.id,
                            user_id=created_user.id,
                            role="member",
                            created_at=now,
                        )
                    )
            self._append_event(
                session=session,
                request_id=row.id,
                actor=actor_id,
                action="User Provisioned",
                reason_or_evidence=f"Provisioned pending user profile for {email}",
            )
            return
        existing.display_name = str(payload.get("display_name") or existing.display_name)
        existing.email = email
        existing.role_summary = normalized_roles or existing.role_summary
        existing.registration_request_id = row.id
        if target_status == RequestStatus.COMPLETED and existing.password_hash and not existing.password_reset_required:
            existing.status = "active"
        elif existing.status == "active":
            existing.status = existing.status
        else:
            existing.status = "pending_activation"
        existing.updated_at = now
        if requested_team is not None:
            membership = session.scalars(
                select(TeamMembershipTable).where(
                    TeamMembershipTable.tenant_id == row.tenant_id,
                    TeamMembershipTable.team_id == requested_team.id,
                    TeamMembershipTable.user_id == existing.id,
                )
            ).first()
            if membership is None:
                session.add(
                    TeamMembershipTable(
                        id=f"tm_{requested_team.id}_{existing.id}",
                        tenant_id=row.tenant_id,
                        team_id=requested_team.id,
                        user_id=existing.id,
                        role="member",
                        created_at=now,
                    )
                )

    def _ensure_run_for_request(self, session, row: RequestTable, target_status: RequestStatus) -> None:
        if row.current_run_id:
            run_row = session.get(RunTable, row.current_run_id)
            if run_row is not None:
                return
        now = datetime.now(timezone.utc)
        run_id = self._next_run_id(session)
        workflow_name = row.template_id.replace("tmpl_", "").replace("_", " ").title()
        session.add(
            RunTable(
                id=run_id,
                request_id=row.id,
                workflow=f"{workflow_name} Workflow",
                status=RunStatus.QUEUED.value if target_status == RequestStatus.QUEUED else RunStatus.RUNNING.value if target_status == RequestStatus.IN_EXECUTION else RunStatus.WAITING.value,
                current_step="Queue Request" if target_status == RequestStatus.QUEUED else "Execute Governed Workflow" if target_status == RequestStatus.IN_EXECUTION else "Human Review",
                elapsed_time="0m",
                waiting_reason="Awaiting execution slot" if target_status == RequestStatus.QUEUED else "Awaiting reviewer approval" if target_status == RequestStatus.AWAITING_REVIEW else None,
                updated_at=now,
                owner_team=row.owner_team_id or "team_ops",
                workflow_identity=row.workflow_binding_id or f"wf_{row.template_id}_{row.template_version.replace('.', '_')}",
                progress_percent=10 if target_status == RequestStatus.QUEUED else 40 if target_status == RequestStatus.IN_EXECUTION else 80,
                current_step_input_summary=f"Request {row.id} entered {target_status.value}.",
                current_step_output_summary="Governed processing initialized.",
                failure_reason=None,
                command_surface=["Pause", "Resume", "Retry Step", "Cancel Run"],
                steps=[
                    {"id": "step_1", "name": "Queue Request", "status": StepStatus.COMPLETED.value if target_status != RequestStatus.QUEUED else StepStatus.ACTIVE.value, "owner": "system"},
                    {"id": "step_2", "name": "Execute Governed Workflow", "status": StepStatus.ACTIVE.value if target_status == RequestStatus.IN_EXECUTION else StepStatus.PENDING.value, "owner": "agent-runtime"},
                    {"id": "step_3", "name": "Human Review", "status": StepStatus.BLOCKED.value if target_status == RequestStatus.AWAITING_REVIEW else StepStatus.PENDING.value, "owner": "review_queue"},
                ],
                run_context=[["Template", f"{row.template_id}@{row.template_version}"], ["Priority", row.priority], ["Request Status", target_status.value]],
                conversation_thread_id=f"thr_{run_id}",
            )
        )
        row.current_run_id = run_id

    def _dispatch_run_to_runtime(
        self,
        session,
        request_row: RequestTable | RequestRecord,
        run_id: str,
        dispatch_type: str,
        actor_id: str,
        force: bool = False,
    ) -> None:
        integration_row = session.scalars(
            select(IntegrationTable).where(
                IntegrationTable.tenant_id == request_row.tenant_id,
                IntegrationTable.type == "runtime",
                IntegrationTable.status == "connected",
            )
        ).first()
        if integration_row is None:
            raise ValueError("No connected runtime integration is available for this tenant")
        existing = session.scalars(
            select(RuntimeDispatchTable).where(
                RuntimeDispatchTable.run_id == run_id,
                RuntimeDispatchTable.dispatch_type == dispatch_type,
            )
        ).first()
        if existing is not None and not force:
            return
        payload = {
            "request_id": request_row.id,
            "run_id": run_id,
            "dispatch_type": dispatch_type,
            "workflow_binding_id": request_row.workflow_binding_id or f"wf_{request_row.template_id}_{request_row.template_version.replace('.', '_')}",
            "template_id": request_row.template_id,
            "template_version": request_row.template_version,
            "priority": request_row.priority,
            "actor_id": actor_id,
        }
        response_payload = runtime_dispatch_service.dispatch(integration_row, payload)
        session.add(
            RuntimeDispatchTable(
                id=self._next_runtime_dispatch_id(session),
                tenant_id=request_row.tenant_id,
                run_id=run_id,
                request_id=request_row.id,
                integration_id=integration_row.id,
                dispatch_type=dispatch_type,
                status=str(response_payload.get("status", "accepted")),
                external_reference=str(response_payload.get("dispatch_id")) if response_payload.get("dispatch_id") else None,
                detail=str(response_payload.get("summary", f"Runtime accepted {dispatch_type} dispatch.")),
                payload=payload,
                response_payload=response_payload,
                dispatched_at=datetime.now(timezone.utc),
            )
        )
        event_store_service.append(
            session,
            tenant_id=request_row.tenant_id,
            event_type=f"runtime.dispatch.{dispatch_type}",
            aggregate_type="run",
            aggregate_id=run_id,
            request_id=request_row.id,
            run_id=run_id,
            actor=actor_id,
            detail=str(response_payload.get("summary", f"Runtime accepted {dispatch_type} dispatch.")),
            payload=payload,
        )
        run_row = session.get(RunTable, run_id)
        if run_row is not None:
            run_row.current_step_output_summary = str(response_payload.get("summary", run_row.current_step_output_summary))
            run_row.run_context = [
                *run_row.run_context,
                ["Runtime Dispatch", dispatch_type],
                ["Runtime Reference", str(response_payload.get("dispatch_id", "accepted"))],
            ]

    def _ensure_artifact_for_request(
        self,
        session,
        row: RequestTable,
        actor_id: str,
        artifact_status: str,
        review_state: str,
        append_version: bool,
    ) -> ArtifactTable:
        artifact_row = session.scalars(select(ArtifactTable).where(ArtifactTable.request_id == row.id).order_by(desc(ArtifactTable.updated_at))).first()
        now = datetime.now(timezone.utc)
        if artifact_row is None:
            artifact_id = self._next_artifact_id(session)
            version_id = self._next_artifact_version_id(session)
            label = "v1"
            content = self._artifact_content_for_request(row, label)
            content_ref = self._artifact_content_ref(artifact_id, version_id)
            object_store_service.put_text(content_ref, content)
            artifact_row = ArtifactTable(
                id=artifact_id,
                type=self._artifact_type_for_request(row),
                name=row.title,
                current_version=label,
                status=artifact_status,
                request_id=row.id,
                updated_at=now,
                owner=row.owner_team_id or "team_ops",
                review_state=review_state,
                promotion_relevant=False,
                versions=[
                    {
                        "id": version_id,
                        "label": label,
                        "status": artifact_status,
                        "created_at": now.isoformat().replace("+00:00", "Z"),
                        "author": actor_id,
                        "summary": f"Initial governed artifact generated for request {row.id}.",
                        "content": content,
                        "content_ref": content_ref,
                    }
                ],
                selected_version_id=version_id,
                stale_review=False,
            )
            session.add(artifact_row)
            self._append_artifact_event(
                session=session,
                artifact_id=artifact_id,
                artifact_version_id=version_id,
                actor=actor_id,
                action="Artifact Created",
                detail=f"Initial artifact {label} created for request {row.id}.",
            )
            self._append_artifact_lineage(
                session=session,
                artifact_id=artifact_id,
                from_version_id=None,
                to_version_id=version_id,
                relation="generated_from_request",
            )
            return artifact_row

        artifact_row.status = artifact_status
        artifact_row.review_state = review_state
        artifact_row.updated_at = now
        if append_version:
            versions = [dict(version) for version in artifact_row.versions]
            next_version_number = len(versions) + 1
            label = f"v{next_version_number}"
            version_id = self._next_artifact_version_id(session)
            content = self._artifact_content_for_request(row, label)
            content_ref = self._artifact_content_ref(artifact_row.id, version_id)
            object_store_service.put_text(content_ref, content)
            if versions and versions[-1]["status"] not in {"approved", "promoted", "completed"}:
                versions[-1]["status"] = "superseded"
            versions.append(
                {
                    "id": version_id,
                    "label": label,
                    "status": artifact_status,
                    "created_at": now.isoformat().replace("+00:00", "Z"),
                    "author": actor_id,
                    "summary": f"Governed artifact advanced to {artifact_status}.",
                    "content": content,
                    "content_ref": content_ref,
                }
            )
            artifact_row.versions = versions
            artifact_row.current_version = label
            artifact_row.selected_version_id = version_id
            self._append_artifact_event(
                session=session,
                artifact_id=artifact_row.id,
                artifact_version_id=version_id,
                actor=actor_id,
                action="Artifact Version Created",
                detail=f"Artifact advanced to {label} with status {artifact_status}.",
            )
            self._append_artifact_lineage(
                session=session,
                artifact_id=artifact_row.id,
                from_version_id=versions[-2]["id"] if len(versions) > 1 else None,
                to_version_id=version_id,
                relation="supersedes",
            )
        else:
            versions = [dict(version) for version in artifact_row.versions]
            if versions:
                versions[-1]["status"] = artifact_status
                artifact_row.versions = versions
        return artifact_row

    def _update_artifact_review_state(
        self,
        session,
        request_id: str,
        artifact_status: str,
        review_state: str,
        stale_review: bool,
        promotion_relevant: bool | None = None,
    ) -> None:
        artifact_row = session.scalars(select(ArtifactTable).where(ArtifactTable.request_id == request_id).order_by(desc(ArtifactTable.updated_at))).first()
        if artifact_row is None:
            return
        artifact_row.status = artifact_status
        artifact_row.review_state = review_state
        artifact_row.stale_review = stale_review
        artifact_row.updated_at = datetime.now(timezone.utc)
        if promotion_relevant is not None:
            artifact_row.promotion_relevant = promotion_relevant
        versions = [dict(version) for version in artifact_row.versions]
        if versions:
            versions[-1]["status"] = artifact_status
            artifact_row.versions = versions
            self._append_artifact_event(
                session=session,
                artifact_id=artifact_row.id,
                artifact_version_id=versions[-1]["id"],
                actor="system",
                action="Artifact Status Updated",
                detail=f"Artifact status updated to {artifact_status}.",
            )

    @staticmethod
    def _artifact_type_for_request(row: RequestTable) -> str:
        if "assessment" in row.template_id or "assessment" in row.request_type:
            return "assessment"
        return "curriculum_unit"

    @staticmethod
    def _artifact_content_for_request(row: RequestTable, version_label: str) -> str:
        return (
            f"{row.title}\n"
            f"Version: {version_label}\n"
            f"Template: {row.template_id}@{row.template_version}\n"
            f"Summary: {row.summary}\n"
        )

    @staticmethod
    def _artifact_content_ref(artifact_id: str, version_id: str) -> str:
        return f"artifacts/{artifact_id}/{version_id}.txt"

    def _append_artifact_event(
        self,
        session,
        artifact_id: str,
        artifact_version_id: str | None,
        actor: str,
        action: str,
        detail: str,
    ) -> None:
        artifact_row = session.get(ArtifactTable, artifact_id)
        session.add(
            ArtifactEventTable(
                artifact_id=artifact_id,
                artifact_version_id=artifact_version_id,
                timestamp=datetime.now(timezone.utc),
                actor=actor,
                action=action,
                detail=detail,
            )
        )
        if artifact_row is not None:
            request_row = session.get(RequestTable, artifact_row.request_id)
            request = request_row and self._request_from_row(request_row) or get_request_state(artifact_row.request_id, None)
            if request is not None:
                event_store_service.append(
                    session,
                    tenant_id=request.tenant_id,
                    event_type="artifact.event_recorded",
                    aggregate_type="artifact",
                    aggregate_id=artifact_id,
                    request_id=request.id,
                    artifact_id=artifact_id,
                    actor=actor,
                    detail=action,
                    payload={"artifact_version_id": artifact_version_id, "message": detail},
                )

    @staticmethod
    def _append_artifact_lineage(
        session,
        artifact_id: str,
        from_version_id: str | None,
        to_version_id: str,
        relation: str,
    ) -> None:
        session.add(
            ArtifactLineageEdgeTable(
                artifact_id=artifact_id,
                from_version_id=from_version_id,
                to_version_id=to_version_id,
                relation=relation,
                created_at=datetime.now(timezone.utc),
            )
        )

    @staticmethod
    def _update_review_queue_status(session, request_id: str, blocking_status: str) -> None:
        queue_row = session.scalars(select(ReviewQueueTable).where(ReviewQueueTable.request_id == request_id).order_by(desc(ReviewQueueTable.id))).first()
        if queue_row is not None:
            queue_row.blocking_status = blocking_status
            queue_row.stale = blocking_status == "Changes requested"

    def _ensure_review_queue_item(self, session, row: RequestTable) -> None:
        routing = dict((row.policy_context or {}).get("routing") or {})
        assigned_reviewer = (routing.get("reviewers") or [row.owner_team_id or "reviewer_queue"])[0]
        existing = session.scalars(select(ReviewQueueTable).where(ReviewQueueTable.request_id == row.id)).first()
        if existing is not None:
            existing.blocking_status = "Blocking request progress"
            existing.stale = False
            existing.assigned_reviewer = assigned_reviewer
            return
        session.add(
            ReviewQueueTable(
                id=self._next_review_queue_id(session),
                request_id=row.id,
                review_scope="artifact_version",
                artifact_or_changeset=f"{row.title} review package",
                type="governance_review",
                priority=row.priority,
                sla="Due in 4h",
                blocking_status="Blocking request progress",
                assigned_reviewer=assigned_reviewer,
                stale=False,
            )
        )

    def _ensure_promotion_record(self, session, row: RequestTable, actor_id: str) -> None:
        routing = dict((row.policy_context or {}).get("routing") or {})
        promotion_approvers = routing.get("promotion_approvers") or [row.owner_team_id or "ops_reviewer"]
        existing = session.scalars(select(PromotionTable).where(PromotionTable.request_id == row.id)).first()
        if existing is not None:
            existing.required_approvals = [
                {"reviewer": approver, "state": "pending", "scope": "promotion"} for approver in promotion_approvers
            ]
            policy_check_service.ensure_promotion_check_records(session, existing, actor_id)
            policy_check_service.sync_promotion_checks(session, existing)
            existing.execution_readiness = self._promotion_readiness_from_db(session, existing)
            return
        promotion = PromotionTable(
            id=self._next_promotion_id(session),
            request_id=row.id,
            target="Production Governance Target",
            strategy="Governed direct promotion",
            required_checks=[],
            required_approvals=[
                {"reviewer": approver, "state": "pending", "scope": "promotion"} for approver in promotion_approvers
            ],
            stale_warnings=[],
            execution_readiness="Blocked until pending checks and approvals are satisfied.",
            promotion_history=[
                {
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "actor": actor_id,
                    "action": "Promotion request created",
                }
            ],
        )
        session.add(promotion)
        session.flush()
        policy_check_service.ensure_promotion_check_records(session, promotion, actor_id)
        policy_check_service.sync_promotion_checks(session, promotion)
        promotion.execution_readiness = self._promotion_readiness_from_db(session, promotion)

    def _promotion_ready(self, check_rows, override_rows, approvals: list[dict]) -> bool:
        return policy_check_service.promotion_ready(check_rows, override_rows, approvals)

    def _promotion_readiness(self, check_rows, override_rows, approvals: list[dict]) -> str:
        return policy_check_service.promotion_readiness(check_rows, override_rows, approvals)

    def _promotion_readiness_from_db(self, session, promotion_row: PromotionTable) -> str:
        return policy_check_service.promotion_readiness_from_db(session, promotion_row)

    @staticmethod
    def _next_action_for_request(status: RequestStatus, has_run: bool, has_promotion: bool) -> str:
        if status == RequestStatus.DRAFT:
            return "Submit request"
        if status == RequestStatus.SUBMITTED:
            return "Validate request"
        if status == RequestStatus.VALIDATION_FAILED:
            return "Amend request"
        if status == RequestStatus.VALIDATED:
            return "Classify request"
        if status == RequestStatus.CLASSIFIED:
            return "Resolve ownership"
        if status == RequestStatus.OWNERSHIP_RESOLVED:
            return "Plan workflow"
        if status == RequestStatus.PLANNED:
            return "Queue execution"
        if status == RequestStatus.QUEUED:
            return "Start governed run" if has_run else "Create governed run"
        if status == RequestStatus.IN_EXECUTION:
            return "Monitor active run"
        if status == RequestStatus.AWAITING_INPUT:
            return "Provide required input"
        if status in {RequestStatus.AWAITING_REVIEW, RequestStatus.UNDER_REVIEW}:
            return "Complete review"
        if status == RequestStatus.CHANGES_REQUESTED:
            return "Revise and resubmit"
        if status == RequestStatus.APPROVED:
            return "Prepare promotion or completion"
        if status == RequestStatus.PROMOTION_PENDING:
            return "Resolve promotion gate" if has_promotion else "Create promotion gate"
        if status == RequestStatus.PROMOTED:
            return "Complete request"
        if status == RequestStatus.FAILED:
            return "Re-plan or cancel request"
        if status == RequestStatus.COMPLETED:
            return "Review completed record"
        if status == RequestStatus.CANCELED:
            return "No action required"
        if status == RequestStatus.ARCHIVED:
            return "Inspect archived record"
        if status == RequestStatus.REJECTED:
            return "Decide whether to supersede or cancel"
        return "Monitor request"

    @staticmethod
    def _artifact_record_from_row(row: ArtifactTable) -> ArtifactRecord:
        return ArtifactRecord.model_validate(
            {
                "id": row.id,
                "type": row.type,
                "name": row.name,
                "current_version": row.current_version,
                "status": row.status,
                "request_id": row.request_id,
                "updated_at": row.updated_at.isoformat().replace("+00:00", "Z"),
                "owner": row.owner,
                "review_state": row.review_state,
                "promotion_relevant": row.promotion_relevant,
            }
        )

    @staticmethod
    def _check_run_from_row(row: CheckRunTable) -> CheckRunRecord:
        return CheckRunRecord.model_validate(
            {
                "id": row.id,
                "request_id": row.request_id,
                "promotion_id": row.promotion_id,
                "scope": row.scope,
                "status": row.status,
                "trigger_reason": row.trigger_reason,
                "enqueued_by": row.enqueued_by,
                "worker_task_id": row.worker_task_id,
                "error_message": row.error_message,
                "queued_at": row.queued_at.isoformat().replace("+00:00", "Z"),
                "started_at": row.started_at.isoformat().replace("+00:00", "Z") if row.started_at else None,
                "completed_at": row.completed_at.isoformat().replace("+00:00", "Z") if row.completed_at else None,
            }
        )

    @staticmethod
    def _event_ledger_record_from_row(row: EventStoreTable) -> EventLedgerRecord:
        return EventLedgerRecord.model_validate(
            {
                "id": row.id,
                "tenant_id": row.tenant_id,
                "event_type": row.event_type,
                "aggregate_type": row.aggregate_type,
                "aggregate_id": row.aggregate_id,
                "request_id": row.request_id,
                "run_id": row.run_id,
                "artifact_id": row.artifact_id,
                "promotion_id": row.promotion_id,
                "check_run_id": row.check_run_id,
                "actor": row.actor,
                "detail": row.detail,
                "payload": row.payload or {},
                "occurred_at": row.occurred_at.isoformat().replace("+00:00", "Z"),
            }
        )

    @staticmethod
    def _event_ledger_record_from_request_event_item(item: dict) -> EventLedgerRecord:
        event_id = str(item.get("event_id") or item.get("SK") or uuid4().hex)
        synthetic_id = -int(event_id.replace("-", "")[:12], 16)
        return EventLedgerRecord.model_validate(
            {
                "id": synthetic_id,
                "tenant_id": item["tenant_id"],
                "event_type": "request.event_recorded",
                "aggregate_type": "request",
                "aggregate_id": item["request_id"],
                "request_id": item["request_id"],
                "run_id": None,
                "artifact_id": None,
                "promotion_id": None,
                "check_run_id": None,
                "actor": item["actor"],
                "detail": item["action"],
                "payload": {"reason_or_evidence": item.get("reason_or_evidence")},
                "occurred_at": item["timestamp"],
            }
        )

    @staticmethod
    def _event_outbox_record_from_row(row: EventOutboxTable) -> EventOutboxRecord:
        return EventOutboxRecord.model_validate(
            {
                "id": row.id,
                "event_store_id": row.event_store_id,
                "tenant_id": row.tenant_id,
                "topic": row.topic,
                "partition_key": row.partition_key,
                "payload": row.payload or {},
                "status": row.status,
                "backend": row.backend,
                "error_message": row.error_message,
                "created_at": row.created_at.isoformat().replace("+00:00", "Z"),
                "published_at": row.published_at.isoformat().replace("+00:00", "Z") if row.published_at else None,
            }
        )

    @staticmethod
    def _provider_for_integration(row: IntegrationTable | None) -> str | None:
        if row is None:
            return None
        settings = row.settings or {}
        configured = settings.get("provider")
        if isinstance(configured, str) and configured:
            return configured
        lowered = row.name.lower()
        if "copilot" in lowered or "microsoft" in lowered:
            return "microsoft"
        if "codex" in lowered or "openai" in lowered:
            return "openai"
        if "claude" in lowered or "anthropic" in lowered:
            return "anthropic"
        return None

    @staticmethod
    def _runtime_subtype_for_integration(row: IntegrationTable | None) -> str | None:
        if row is None:
            return None
        configured = (row.settings or {}).get("runtime_subtype")
        if isinstance(configured, str) and configured.strip():
            return configured.strip().lower()
        provider = (row.settings or {}).get("provider")
        if isinstance(provider, str) and provider.strip().lower() == "sbcl-agent":
            return "sbcl_agent"
        return None

    def _session_kind_for_integration(self, row: IntegrationTable | None) -> str:
        return "stateful_runtime" if self._runtime_subtype_for_integration(row) == "sbcl_agent" else "interactive_agent"

    def _governed_runtime_summary(
        self,
        row: AgentSessionTable,
        integration_row: IntegrationTable | None,
        bundle: ContextBundleRecord | None = None,
    ) -> GovernedRuntimeSummary | None:
        runtime_subtype = self._runtime_subtype_for_integration(integration_row)
        if runtime_subtype != "sbcl_agent":
            return None
        contents = bundle.contents if bundle and isinstance(bundle.contents, dict) else {}
        runtime_binding = contents.get("sbcl_agent_runtime", {}) if isinstance(contents.get("sbcl_agent_runtime", {}), dict) else {}
        binding = contents.get("sbcl_agent_binding", {}) if isinstance(contents.get("sbcl_agent_binding", {}), dict) else {}
        approvals = list(contents.get("sbcl_agent_approvals", [])) if isinstance(contents.get("sbcl_agent_approvals", []), list) else []
        artifacts = list(contents.get("sbcl_agent_artifacts", [])) if isinstance(contents.get("sbcl_agent_artifacts", []), list) else []
        external_bindings = list(contents.get("external_bindings", [])) if isinstance(contents.get("external_bindings", []), list) else []
        return GovernedRuntimeSummary(
            runtime_subtype=runtime_subtype,
            session_kind=self._session_kind_for_integration(integration_row),
            adapter_type="sbcl_agent_runtime",
            environment_ref=runtime_binding.get("environment_id") or runtime_binding.get("environment_ref") or binding.get("environment_ref") or row.external_session_ref,
            thread_ref=runtime_binding.get("active_thread_id") or runtime_binding.get("thread_ref") or f"thread:{row.id}",
            turn_ref=runtime_binding.get("turn_ref") or f"turn:{row.id}:latest",
            pending_approval_count=int(runtime_binding.get("pending_approval_count") or len(approvals) or (1 if row.status == "waiting_on_human" else 0)),
            pending_artifact_count=int(runtime_binding.get("pending_artifact_count") or len(artifacts) or 0),
            external_bindings=external_bindings,
        )

    def _sbcl_agent_dispatch_payload(
        self,
        row: AgentSessionTable,
        integration_row: IntegrationTable,
    ) -> dict:
        return {
            "request_id": row.request_id,
            "run_id": row.id,
            "integration_id": integration_row.id,
            "actor_id": row.assigned_by,
            "metadata": {
                "tenant_id": row.tenant_id,
                "projection_id": f"projection:{row.id}",
                "agent_session_id": row.id,
            },
        }

    def _ensure_sbcl_agent_environment_ref(
        self,
        row: AgentSessionTable,
        integration_row: IntegrationTable | None,
    ) -> str | None:
        if self._runtime_subtype_for_integration(integration_row) != "sbcl_agent" or integration_row is None:
            return row.external_session_ref
        if row.external_session_ref:
            return row.external_session_ref
        default_ref = runtime_dispatch_service.sbcl_agent_environment_ref(row.request_id, row.id)
        try:
            response = runtime_dispatch_service.dispatch(integration_row, self._sbcl_agent_dispatch_payload(row, integration_row))
            return str(response.get("external_reference") or default_ref)
        except Exception:
            return default_ref

    def _sbcl_agent_bundle_state(
        self,
        row: AgentSessionTable,
        integration_row: IntegrationTable | None,
    ) -> dict:
        environment_ref = self._ensure_sbcl_agent_environment_ref(row, integration_row)
        fallback_runtime = {
            "environment_ref": environment_ref,
            "thread_ref": f"thread:{row.id}",
            "turn_ref": f"turn:{row.id}:latest",
            "pending_approval_count": 1 if row.status == "waiting_on_human" else 0,
            "pending_artifact_count": 0,
            "runtime_subtype": "sbcl_agent",
            "session_kind": "stateful_runtime",
        }
        if not environment_ref:
            return {"binding": {}, "governed_runtime": fallback_runtime, "approvals": [], "artifacts": [], "snapshot": {}, "warning": None}
        try:
            snapshot = runtime_dispatch_service.export_sbcl_agent_snapshot(environment_ref)
            approvals = list(snapshot.get("approvals") or [])
            artifacts = list(snapshot.get("artifacts") or [])
            binding = dict(snapshot.get("binding") or {})
            governed_runtime = dict(snapshot.get("governed_runtime") or {})
            governed_runtime.setdefault("environment_ref", environment_ref)
            governed_runtime.setdefault("thread_ref", snapshot.get("thread", {}).get("id") if isinstance(snapshot.get("thread"), dict) else None)
            governed_runtime.setdefault("turn_ref", snapshot.get("turn", {}).get("id") if isinstance(snapshot.get("turn"), dict) else None)
            governed_runtime["pending_approval_count"] = len(approvals)
            governed_runtime["pending_artifact_count"] = len(artifacts)
            return {
                "binding": binding,
                "governed_runtime": governed_runtime,
                "approvals": approvals,
                "artifacts": artifacts,
                "snapshot": snapshot,
                "warning": None,
            }
        except Exception as exc:
            return {
                "binding": {"environment_ref": environment_ref},
                "governed_runtime": fallback_runtime,
                "approvals": [],
                "artifacts": [],
                "snapshot": {},
                "warning": f"Live sbcl-agent snapshot unavailable: {exc}",
            }

    @staticmethod
    def _normalize_artifact_key(value: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-._")
        return normalized or "artifact"

    @staticmethod
    def _artifact_import_defaults(payload: ImportAgentSessionArtifactRequest) -> dict:
        return {
            "status": "imported",
            "review_state": "pending",
            "promotion_relevant": payload.promotion_relevant,
        }

    def _refresh_agent_session_context(
        self,
        request_id: str,
        session_id: str,
        tenant_id: str,
        actor_id: str,
        integration_row: IntegrationTable,
        collaboration_mode: str = "agent_assisted",
        agent_operating_profile: str = "general",
        session_row: AgentSessionTable | None = None,
    ) -> ContextBundleRecord:
        bundle = context_bundle_service.assemble_bundle(
            request_id=request_id,
            session_id=session_id,
            bundle_type="agent_session",
            assembled_by=actor_id,
            tenant_id=tenant_id,
        )
        tools, restricted_tools, degraded_tools, warnings = self._build_agent_session_tools(
            integration_row=integration_row,
            bundle=bundle,
            collaboration_mode=collaboration_mode,
            agent_operating_profile=agent_operating_profile,
        )
        policy_scope = {
            "collaboration_mode": collaboration_mode,
            "agent_operating_profile": agent_operating_profile,
            "allowed_content_keys": [
                "request_data",
                "template_semantics",
                "workflow_state",
                "policy_constraints",
                "prior_decisions",
                "relationship_graph",
                "available_tools",
                "external_bindings",
            ],
            "tool_names": [tool.name for tool in tools],
            "restricted_tool_names": [tool.name for tool in restricted_tools],
            "degraded_tool_names": [tool.name for tool in degraded_tools],
            "warnings": warnings,
        }
        scoped_bundle = context_bundle_service.scope_bundle(bundle.id, policy_scope)
        contents = dict(scoped_bundle.contents or {})
        contents["available_tools"] = [tool.model_dump(mode="json") for tool in tools]
        contents["restricted_tools"] = [tool.model_dump(mode="json") for tool in restricted_tools]
        contents["degraded_tools"] = [tool.model_dump(mode="json") for tool in degraded_tools]
        runtime_subtype = self._runtime_subtype_for_integration(integration_row)
        session_kind = self._session_kind_for_integration(integration_row)
        contents["external_bindings"] = [
            {
                "integration_id": integration_row.id,
                "integration_name": integration_row.name,
                "provider": self._provider_for_integration(integration_row),
                "endpoint": integration_security_service.setting(integration_row, "base_url") or integration_row.endpoint,
                "runtime_subtype": runtime_subtype,
                "session_kind": session_kind,
            }
        ]
        if runtime_subtype == "sbcl_agent":
            active_session_row = session_row
            if active_session_row is None:
                with SessionLocal() as lookup_session:
                    active_session_row = lookup_session.get(AgentSessionTable, session_id)
            if active_session_row is not None:
                live_state = self._sbcl_agent_bundle_state(active_session_row, integration_row)
                contents["sbcl_agent_binding"] = live_state.get("binding") or {}
                contents["sbcl_agent_runtime"] = live_state.get("governed_runtime") or {}
                contents["sbcl_agent_approvals"] = live_state.get("approvals") or []
                contents["sbcl_agent_artifacts"] = live_state.get("artifacts") or []
                if live_state.get("snapshot"):
                    contents["sbcl_agent_snapshot"] = live_state.get("snapshot")
                if live_state.get("warning"):
                    warnings = [*warnings, live_state["warning"]]
            else:
                contents["sbcl_agent_runtime"] = {
                    "environment_ref": f"environment:{session_id}",
                    "thread_ref": f"thread:{session_id}",
                    "turn_ref": f"turn:{session_id}:latest",
                    "pending_approval_count": 0,
                    "pending_artifact_count": 0,
                }
            policy_scope["warnings"] = warnings
        with SessionLocal() as session:
            row = session.get(ContextBundleTable, scoped_bundle.id)
            if row is not None:
                row.contents = contents
                session.commit()
                session.refresh(row)
                scoped_bundle = ContextBundleRecord.model_validate(row)
        context_bundle_service.record_access(
            bundle_id=scoped_bundle.id,
            accessor_type="human",
            accessor_id=actor_id,
            resource="context_bundle",
            result="granted",
            policy_basis=policy_scope,
        )
        return scoped_bundle

    def _build_agent_session_tools(
        self,
        integration_row: IntegrationTable,
        bundle: ContextBundleRecord,
        collaboration_mode: str = "agent_assisted",
        agent_operating_profile: str = "general",
    ) -> tuple[list[AgentSessionToolRecord], list[AgentSessionToolRecord], list[AgentSessionToolRecord], list[str]]:
        request_payload = (bundle.contents or {}).get("request_data", {}) if isinstance(bundle.contents, dict) else {}
        base_tools: list[dict] = [
            {
                "name": "request.summary",
                "description": "Read the governed request summary, payload, and lifecycle state.",
                "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "request.relationships",
                "description": "Inspect dependency and related-request context from the governed graph.",
                "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "request.prior_decisions",
                "description": "Review prior governance and review decisions attached to this request.",
                "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "request.timeline",
                "description": "Inspect the governed request and workflow timeline.",
                "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
                "required_collaboration_mode": "agent_assisted",
            },
            {
                "name": "request.policy_context",
                "description": "Inspect policy constraints, routing context, and collaboration governance on the request.",
                "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
                "required_collaboration_mode": "agent_assisted",
            },
        ]
        if self._runtime_subtype_for_integration(integration_row) == "sbcl_agent":
            base_tools.extend([
                {
                    "name": "runtime.environment",
                    "description": "Inspect projected sbcl-agent environment, thread, and turn bindings.",
                    "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
                    "required_collaboration_mode": "agent_assisted",
                },
                {
                    "name": "runtime.approvals",
                    "description": "Inspect governed runtime approval checkpoints and resumable work.",
                    "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
                    "required_collaboration_mode": "agent_assisted",
                },
                {
                    "name": "runtime.artifacts",
                    "description": "Inspect importable artifacts projected from sbcl-agent runtime work.",
                    "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
                    "required_collaboration_mode": "agent_assisted",
                },
            ])
        discovered_tools = mcp_tool_registry.discover_tools(
            session_context={
                "tenant_id": bundle.tenant_id,
                "request_id": bundle.request_id,
                "session_id": bundle.session_id,
                "collaboration_mode": collaboration_mode,
            }
        )
        tool_map = {tool["name"]: tool for tool in base_tools}
        for tool in discovered_tools:
            tool_map.setdefault(tool["name"], tool)
        policy_rules = self._derive_agent_session_tool_policy(
            request_payload,
            integration_row,
            collaboration_mode,
            agent_operating_profile,
        )
        allowed_tools = filter_tools_by_policy(
            tools=list(tool_map.values()),
            collaboration_mode=collaboration_mode,
            role="agent",
            policy_rules=policy_rules,
        )
        allowed_tool_names = {tool.get("name", "") for tool in allowed_tools}
        restricted_tools: list[AgentSessionToolRecord] = []
        degraded_tools: list[AgentSessionToolRecord] = []
        available_records: list[AgentSessionToolRecord] = []
        for tool in tool_map.values():
            name = tool.get("name", "")
            restriction_reason = self._tool_restriction_reason(
                tool=tool,
                collaboration_mode=collaboration_mode,
                role="agent",
                policy_rules=policy_rules,
            )
            degraded_reason = self._tool_degradation_reason(tool=tool, bundle=bundle)
            if name not in allowed_tool_names:
                restricted_tools.append(
                    AgentSessionToolRecord(
                        name=name,
                        description=tool.get("description", ""),
                        input_schema=tool.get("input_schema", {}),
                        required_collaboration_mode=tool.get("required_collaboration_mode"),
                        allowed_roles=list(tool.get("allowed_roles", [])),
                        availability="denied",
                        availability_reason=restriction_reason,
                    )
                )
                continue
            record = AgentSessionToolRecord(
                name=name,
                description=tool.get("description", ""),
                input_schema=tool.get("input_schema", {}),
                required_collaboration_mode=tool.get("required_collaboration_mode"),
                allowed_roles=list(tool.get("allowed_roles", [])),
                availability="degraded" if degraded_reason else "available",
                availability_reason=degraded_reason,
            )
            if degraded_reason:
                degraded_tools.append(record)
            else:
                available_records.append(record)
        warnings: list[str] = []
        if self._provider_for_integration(integration_row) is None:
            warnings.append("The selected integration does not declare a provider for governed MCP access.")
        if collaboration_mode == "human_led":
            warnings.append("Human-led mode sharply limits agent autonomy and MCP capability access.")
        if agent_operating_profile != "general":
            warnings.append(f"Agent operating profile '{agent_operating_profile}' is active for this session.")
        if self._runtime_subtype_for_integration(integration_row) == "sbcl_agent":
            warnings.append("This governed session is bound to a stateful sbcl-agent runtime and supports runtime resume/import workflows.")
        if not allowed_tool_names:
            warnings.append("No MCP capabilities are currently available for this session.")
        if degraded_tools:
            warnings.append("Some MCP capabilities are degraded because governed context is incomplete for this session.")
        return (available_records, restricted_tools, degraded_tools, warnings)

    @staticmethod
    def _tool_restriction_reason(
        tool: dict,
        collaboration_mode: str,
        role: str,
        policy_rules: list[dict],
    ) -> str:
        name = tool.get("name", "")
        for rule in policy_rules:
            for action in rule.get("actions", []):
                if action.get("type") != "restrict_tool" or action.get("tool_name") != name:
                    continue
                restrict_mode = action.get("collaboration_mode")
                restrict_role = action.get("role")
                mode_match = restrict_mode is None or restrict_mode == collaboration_mode
                role_match = restrict_role is None or restrict_role == role
                if mode_match and role_match:
                    return action.get("reason") or "Restricted by session policy."
        required_mode = tool.get("required_collaboration_mode")
        if required_mode and not _mode_satisfies(collaboration_mode, required_mode):
            return f"Requires collaboration mode '{required_mode}' or higher."
        allowed_roles = tool.get("allowed_roles")
        if allowed_roles and role not in allowed_roles:
            return f"Restricted to roles: {', '.join(allowed_roles)}."
        return "Restricted by governed session policy."

    @staticmethod
    def _tool_degradation_reason(tool: dict, bundle: ContextBundleRecord) -> str | None:
        contents = bundle.contents if isinstance(bundle.contents, dict) else {}
        request_data = contents.get("request_data", {}) if isinstance(contents.get("request_data", {}), dict) else {}
        tool_name = tool.get("name")
        if tool_name == "request.summary" and not request_data:
            return "Governed request summary data is not currently available."
        if tool_name == "request.relationships" and not contents.get("relationship_graph"):
            return "No governed request relationships are currently attached."
        if tool_name == "request.prior_decisions" and not contents.get("prior_decisions"):
            return "No prior governance decisions are currently attached."
        if tool_name == "request.timeline" and not contents.get("workflow_state"):
            return "Workflow timeline state is currently unavailable."
        if tool_name == "request.policy_context" and not request_data.get("policy_context"):
            return "No explicit policy context is currently attached to the request."
        if tool_name == "runtime.environment" and not contents.get("sbcl_agent_runtime"):
            return "No sbcl-agent runtime binding has been projected for this session yet."
        if tool_name == "runtime.approvals" and not contents.get("sbcl_agent_runtime"):
            return "Runtime checkpoint data is not currently available."
        if tool_name == "runtime.artifacts" and not contents.get("sbcl_agent_runtime"):
            return "No importable sbcl-agent artifact summaries are currently attached."
        return None

    @staticmethod
    def _derive_agent_session_tool_policy(
        request_payload: dict,
        integration_row: IntegrationTable,
        collaboration_mode: str,
        agent_operating_profile: str,
    ) -> list[dict]:
        policy_context = request_payload.get("policy_context", {}) if isinstance(request_payload, dict) else {}
        actions: list[dict] = []
        if collaboration_mode == "human_led" or policy_context.get("collaboration_mode") == "human_led":
            actions.append({"type": "restrict_tool", "tool_name": "request.timeline"})
            actions.append({"type": "restrict_tool", "tool_name": "request.policy_context"})
        if agent_operating_profile == "editorial":
            actions.append({"type": "restrict_tool", "tool_name": "request.relationships"})
        if agent_operating_profile == "execution":
            actions.append({"type": "restrict_tool", "tool_name": "request.prior_decisions"})
        if agent_operating_profile == "review":
            actions.append({"type": "restrict_tool", "tool_name": "request.relationships"})
        if integration_row.status != "connected":
            actions.append({"type": "restrict_tool", "tool_name": "request.timeline"})
        if ((integration_row.settings or {}).get("runtime_subtype") or "").strip().lower() == "sbcl_agent" and collaboration_mode == "human_led":
            actions.append({"type": "restrict_tool", "tool_name": "runtime.environment"})
            actions.append({"type": "restrict_tool", "tool_name": "runtime.approvals"})
            actions.append({"type": "restrict_tool", "tool_name": "runtime.artifacts"})
        return [{"actions": actions}] if actions else []

    def _validate_integration_configuration(self, integration_type: str, endpoint: str, settings_dict: dict | None) -> None:
        provider = None
        if isinstance(settings_dict, dict):
            configured = settings_dict.get("provider")
            provider = configured.strip().lower() if isinstance(configured, str) and configured.strip() else None

        if provider == "openai":
            base_url = integration_security_service.setting(SimpleNamespace(settings=settings_dict), "base_url") or "https://api.openai.com/v1"
            integration_security_service.validate_outbound_target(
                base_url,
                allowed_hosts=settings.integration_openai_allowed_hosts,
                allow_http_loopback=settings.integration_allow_http_loopback,
            )
        elif provider == "anthropic":
            base_url = integration_security_service.setting(SimpleNamespace(settings=settings_dict), "base_url") or "https://api.anthropic.com/v1"
            integration_security_service.validate_outbound_target(
                base_url,
                allowed_hosts=settings.integration_anthropic_allowed_hosts,
                allow_http_loopback=settings.integration_allow_http_loopback,
            )
        elif provider == "microsoft":
            base_url = integration_security_service.setting(SimpleNamespace(settings=settings_dict), "base_url") or "https://graph.microsoft.com/beta/copilot"
            integration_security_service.validate_outbound_target(
                base_url,
                allowed_hosts=settings.integration_microsoft_allowed_hosts,
                allow_http_loopback=settings.integration_allow_http_loopback,
            )

        if integration_type == "runtime" and endpoint.startswith(("http://", "https://")):
            integration_security_service.validate_outbound_target(
                endpoint,
                allowed_hosts=settings.integration_runtime_allowed_hosts,
                allow_http_loopback=settings.integration_allow_http_loopback,
            )
        if integration_type == "deployment" and endpoint.startswith(("http://", "https://")):
            integration_security_service.validate_outbound_target(
                endpoint,
                allowed_hosts=settings.integration_deployment_allowed_hosts,
                allow_http_loopback=settings.integration_allow_http_loopback,
            )

    @staticmethod
    def _agent_message_from_row(row: AgentSessionMessageTable) -> AgentSessionMessageRecord:
        return AgentSessionMessageRecord(
            id=row.id,
            session_id=row.session_id,
            request_id=row.request_id,
            sender_type=row.sender_type,
            sender_id=row.sender_id,
            message_type=row.message_type,
            body=row.body,
            created_at=row.created_at.isoformat().replace("+00:00", "Z"),
        )

    def _agent_session_from_row(
        self,
        row: AgentSessionTable,
        integration_row: IntegrationTable | None,
        message_rows: list[AgentSessionMessageTable] | None = None,
    ) -> AgentSessionRecord:
        ordered_messages = list(sorted(message_rows or [], key=lambda item: item.created_at))
        latest_message = self._agent_message_from_row(ordered_messages[-1]) if ordered_messages else None
        return AgentSessionRecord(
            id=row.id,
            request_id=row.request_id,
            integration_id=row.integration_id,
            integration_name=integration_row.name if integration_row else row.integration_id,
            agent_label=row.agent_label,
            collaboration_mode=row.collaboration_mode,
            agent_operating_profile=row.agent_operating_profile,
            provider=self._provider_for_integration(integration_row),
            runtime_subtype=self._runtime_subtype_for_integration(integration_row),
            session_kind=self._session_kind_for_integration(integration_row),
            status=row.status,
            awaiting_human=row.awaiting_human,
            summary=row.summary,
            external_session_ref=row.external_session_ref,
            resume_request_status=row.resume_request_status,
            assigned_by=row.assigned_by,
            assigned_at=row.assigned_at.isoformat().replace("+00:00", "Z"),
            updated_at=row.updated_at.isoformat().replace("+00:00", "Z"),
            governed_runtime=self._governed_runtime_summary(row, integration_row),
            latest_message=latest_message,
            message_count=len(ordered_messages),
        )

    @staticmethod
    def _agent_transcript_from_rows(rows: list[AgentSessionMessageTable]) -> list[dict[str, str]]:
        transcript: list[dict[str, str]] = []
        for row in sorted(rows, key=lambda item: item.created_at):
            role = "assistant" if row.sender_type == "agent" else "user"
            transcript.append({"role": role, "content": row.body})
        return transcript

    @staticmethod
    def _sbcl_agent_response_text(
        session_row: AgentSessionTable,
        latest_human_message: AgentSessionMessageTable,
        bundle: ContextBundleRecord | None,
    ) -> str:
        contents = bundle.contents if bundle and isinstance(bundle.contents, dict) else {}
        binding = contents.get("sbcl_agent_binding", {}) if isinstance(contents.get("sbcl_agent_binding", {}), dict) else {}
        runtime = contents.get("sbcl_agent_runtime", {}) if isinstance(contents.get("sbcl_agent_runtime", {}), dict) else {}
        approvals = list(contents.get("sbcl_agent_approvals", [])) if isinstance(contents.get("sbcl_agent_approvals", []), list) else []
        artifacts = list(contents.get("sbcl_agent_artifacts", [])) if isinstance(contents.get("sbcl_agent_artifacts", []), list) else []
        environment_ref = binding.get("environment_ref") or session_row.external_session_ref or "<unbound>"
        thread_ref = runtime.get("thread_ref") or runtime.get("active_thread_id") or "unknown"
        turn_ref = runtime.get("turn_ref") or "latest"
        lines = [
            f"{session_row.agent_label} is operating as a governed sbcl-agent runtime.",
            f"Environment ref: {environment_ref}",
            f"Thread ref: {thread_ref}",
            f"Turn ref: {turn_ref}",
        ]
        if latest_human_message.message_type != "assignment":
            lines.append(f"Latest guidance: {latest_human_message.body}")
        lines.append(
            "Runtime state: "
            f"approvals={len(approvals)} artifacts={len(artifacts)} "
            f"threads={runtime.get('thread_count', 0)} work_items={runtime.get('work_item_count', 0)} "
            f"incidents={runtime.get('incident_count', 0)}"
        )
        if approvals:
            preview = ", ".join(
                f"{item.get('id', 'work-item')}:{item.get('wait_reason', item.get('status', 'pending'))}"
                for item in approvals[:3]
                if isinstance(item, dict)
            )
            lines.append(f"Pending approvals: {preview}")
        else:
            lines.append("Pending approvals: none")
        if artifacts:
            preview = ", ".join(
                item.get("title") or item.get("path") or item.get("id", "artifact")
                for item in artifacts[:3]
                if isinstance(item, dict)
            )
            lines.append(f"Importable artifacts: {preview}")
        else:
            lines.append("Importable artifacts: none")
        lines.append("Use runtime.environment, runtime.approvals, and runtime.artifacts to inspect governed state before resuming or importing.")
        return "\n".join(lines)

    @staticmethod
    def _sbcl_agent_turn_summary(
        session_row: AgentSessionTable,
        bundle: ContextBundleRecord | None,
    ) -> str:
        contents = bundle.contents if bundle and isinstance(bundle.contents, dict) else {}
        approvals = list(contents.get("sbcl_agent_approvals", [])) if isinstance(contents.get("sbcl_agent_approvals", []), list) else []
        artifacts = list(contents.get("sbcl_agent_artifacts", [])) if isinstance(contents.get("sbcl_agent_artifacts", []), list) else []
        if approvals:
            return f"{session_row.agent_label} is waiting on governed runtime approval"
        if artifacts:
            return f"{session_row.agent_label} surfaced governed runtime artifacts for review"
        return f"{session_row.agent_label} refreshed governed runtime state"

    def _artifact_detail_from_row(
        self,
        row: ArtifactTable,
        event_rows: list[ArtifactEventTable] | None = None,
        lineage_rows: list[ArtifactLineageEdgeTable] | None = None,
    ) -> ArtifactDetail:
        versions = []
        for version in row.versions:
            hydrated_version = dict(version)
            content_ref = hydrated_version.get("content_ref")
            if content_ref and object_store_service.exists(content_ref):
                hydrated_version["content"] = object_store_service.get_text(content_ref)
            versions.append(hydrated_version)
        return ArtifactDetail.model_validate(
            {
                "artifact": self._artifact_record_from_row(row),
                "versions": versions,
                "selected_version_id": row.selected_version_id,
                "review_state": row.review_state,
                "stale_review": row.stale_review,
                "history": [
                    ArtifactEvent(
                        timestamp=event_row.timestamp.isoformat().replace("+00:00", "Z"),
                        actor=event_row.actor,
                        action=event_row.action,
                        detail=event_row.detail,
                        artifact_version_id=event_row.artifact_version_id,
                    )
                    for event_row in (event_rows or [])
                ],
                "lineage": [
                    ArtifactLineageEdge(
                        from_version_id=lineage_row.from_version_id,
                        to_version_id=lineage_row.to_version_id,
                        relation=lineage_row.relation,
                        created_at=lineage_row.created_at.isoformat().replace("+00:00", "Z"),
                    )
                    for lineage_row in (lineage_rows or [])
                ],
            }
        )

    @staticmethod
    def _format_timedelta(value: timedelta) -> str:
        total_minutes = max(int(value.total_seconds() // 60), 0)
        hours, minutes = divmod(total_minutes, 60)
        if hours and minutes:
            return f"{hours}h {minutes}m"
        if hours:
            return f"{hours}h"
        return f"{minutes}m"

    @staticmethod
    def _format_percent(numerator: int, denominator: int) -> str:
        if denominator <= 0:
            return "0%"
        return f"{(numerator / denominator) * 100:.0f}%"

    @staticmethod
    def _capability_record_from_row(row: CapabilityTable) -> CapabilityRecord:
        return CapabilityRecord.model_validate(
            {
                "id": row.id,
                "name": row.name,
                "type": row.type,
                "version": row.version,
                "status": row.status,
                "owner": row.owner,
                "updated_at": row.updated_at.isoformat().replace("+00:00", "Z"),
                "usage_count": row.usage_count,
            }
        )

    def _capability_detail_from_row(self, row: CapabilityTable) -> CapabilityDetail:
        return CapabilityDetail.model_validate(
            {
                "capability": self._capability_record_from_row(row),
                "definition": row.definition,
                "lineage": row.lineage,
                "usage": row.usage,
                "performance": row.performance,
                "history": row.history,
            }
        )


governance_repository = GovernanceRepository()
