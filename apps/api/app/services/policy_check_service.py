from datetime import datetime, timezone

from sqlalchemy import desc, select

from app.db.models import ArtifactTable, CheckOverrideTable, CheckResultTable, PromotionTable, RequestTable, ReviewQueueTable, TransitionGateTable
from app.models.request import RequestRecord, RequestStatus


class PolicyCheckService:
    REQUEST_CHECK_DEFINITIONS = (
        ("Intake Completeness", "Awaiting request field validation."),
        ("Review Package Readiness", "Awaiting artifact and reviewer routing."),
        ("Approval Freshness", "Awaiting approved review evidence."),
    )
    PROMOTION_CHECK_DEFINITIONS = (
        ("Policy Bundle", "Awaiting final policy verification."),
        ("Approval Freshness", "Awaiting final approver confirmation."),
    )
    REQUEST_TRANSITION_GATE_TARGETS = {
        status.value
        for status in RequestStatus
        if status not in {RequestStatus.DRAFT, RequestStatus.SUBMITTED, RequestStatus.CANCELED, RequestStatus.ARCHIVED}
    }

    @classmethod
    def parse_request_transition_rules(cls, rules: list[str]) -> list[tuple[str, str]]:
        parsed_rules: list[tuple[str, str]] = []
        allowed_check_names = {name for name, _ in cls.REQUEST_CHECK_DEFINITIONS}
        for raw_rule in rules:
            rule = raw_rule.strip()
            if not rule:
                continue
            if ":" not in rule:
                raise ValueError(f"Invalid rule format: {rule}. Expected 'target_status: Check Name'.")
            transition_target, required_check_name = [part.strip() for part in rule.split(":", 1)]
            if not transition_target or not required_check_name:
                raise ValueError(f"Invalid rule format: {rule}. Expected 'target_status: Check Name'.")
            if transition_target not in cls.REQUEST_TRANSITION_GATE_TARGETS:
                allowed_targets = ", ".join(sorted(cls.REQUEST_TRANSITION_GATE_TARGETS))
                raise ValueError(f"Unknown transition target '{transition_target}'. Allowed targets: {allowed_targets}")
            if required_check_name not in allowed_check_names:
                allowed_checks = ", ".join(sorted(allowed_check_names))
                raise ValueError(f"Unknown check name '{required_check_name}'. Allowed checks: {allowed_checks}")
            parsed_rules.append((transition_target, required_check_name))
        return parsed_rules

    @staticmethod
    def active_transition_gate_check_names(session, target_status: RequestStatus, tenant_id: str) -> set[str]:
        return {
            gate.required_check_name
            for gate in session.scalars(
                select(TransitionGateTable).where(
                    TransitionGateTable.tenant_id == tenant_id,
                    TransitionGateTable.gate_scope == "request",
                    TransitionGateTable.transition_target == target_status.value,
                    TransitionGateTable.active.is_(True),
                )
            ).all()
        }

    @classmethod
    def ensure_request_check_records(cls, session, row: RequestTable | RequestRecord, actor_id: str) -> None:
        existing = session.scalars(select(CheckResultTable).where(CheckResultTable.request_id == row.id, CheckResultTable.promotion_id.is_(None))).all()
        if existing:
            return
        now = datetime.now(timezone.utc)
        for index, (name, detail) in enumerate(cls.REQUEST_CHECK_DEFINITIONS, start=1):
            session.add(
                CheckResultTable(
                    id=f"reqchk_{row.id}_{index}",
                    request_id=row.id,
                    promotion_id=None,
                    name=name,
                    state="pending",
                    detail=detail,
                    severity="required",
                    evidence="Not yet evaluated",
                    evaluated_at=now,
                    evaluated_by=actor_id,
                )
            )
        session.flush()

    @classmethod
    def run_request_checks(cls, session, row: RequestTable | RequestRecord, actor_id: str) -> None:
        cls.ensure_request_check_records(session, row, actor_id)
        artifact_row = session.scalars(select(ArtifactTable).where(ArtifactTable.request_id == row.id).order_by(desc(ArtifactTable.updated_at))).first()
        review_row = session.scalars(select(ReviewQueueTable).where(ReviewQueueTable.request_id == row.id).order_by(desc(ReviewQueueTable.id))).first()
        checks = session.scalars(select(CheckResultTable).where(CheckResultTable.request_id == row.id, CheckResultTable.promotion_id.is_(None)).order_by(CheckResultTable.name)).all()
        now = datetime.now(timezone.utc)
        required_fields = {"title": bool(row.title.strip()), "summary": bool(row.summary.strip()), "template_id": bool(row.template_id.strip())}
        for check in checks:
            if check.name == "Intake Completeness":
                passed = all(required_fields.values())
                check.state = "passed" if passed else "failed"
                check.detail = "All canonical intake fields are populated." if passed else "Title, summary, and template binding are required."
                check.evidence = str(required_fields)
            elif check.name == "Review Package Readiness":
                passed = artifact_row is not None and review_row is not None
                check.state = "passed" if passed else "pending"
                check.detail = "Artifact and review routing are ready." if passed else "Artifact generation and reviewer routing must complete."
                check.evidence = f"artifact={artifact_row.id if artifact_row else 'missing'}, review={review_row.id if review_row else 'missing'}"
            elif check.name == "Approval Freshness":
                passed = artifact_row is not None and not artifact_row.stale_review and (review_row is None or review_row.blocking_status == "Approved")
                check.state = "passed" if passed else "pending"
                check.detail = "Latest approval evidence is fresh." if passed else "A fresh approved review is required before promotion."
                check.evidence = f"artifact_stale={artifact_row.stale_review if artifact_row else 'missing'}, review={review_row.blocking_status if review_row else 'missing'}"
            check.evaluated_at = now
            check.evaluated_by = actor_id

    @classmethod
    def assert_request_transition_ready(cls, session, request_id: str, target_status: RequestStatus, tenant_id: str) -> None:
        required_names = cls.active_transition_gate_check_names(session, target_status, tenant_id)
        if not required_names:
            return
        checks = session.scalars(select(CheckResultTable).where(CheckResultTable.request_id == request_id, CheckResultTable.promotion_id.is_(None))).all()
        checks_by_name = {check.name: check for check in checks}
        unresolved = [name for name in required_names if checks_by_name.get(name) is None or checks_by_name[name].state != "passed"]
        if unresolved:
            joined = ", ".join(sorted(unresolved))
            raise ValueError(f"Request cannot transition to {target_status.value} until checks pass: {joined}")

    @classmethod
    def ensure_promotion_check_records(cls, session, promotion_row: PromotionTable, actor_id: str) -> None:
        existing = session.scalars(select(CheckResultTable).where(CheckResultTable.promotion_id == promotion_row.id)).all()
        if existing:
            return
        now = datetime.now(timezone.utc)
        for index, (name, detail) in enumerate(cls.PROMOTION_CHECK_DEFINITIONS, start=1):
            session.add(
                CheckResultTable(
                    id=f"chk_{promotion_row.id}_{index}",
                    request_id=promotion_row.request_id,
                    promotion_id=promotion_row.id,
                    name=name,
                    state="pending",
                    detail=detail,
                    severity="required",
                    evidence="Not yet evaluated",
                    evaluated_at=now,
                    evaluated_by=actor_id,
                )
            )
        session.flush()

    @classmethod
    def sync_promotion_checks(cls, session, promotion_row: PromotionTable) -> None:
        check_rows = session.scalars(select(CheckResultTable).where(CheckResultTable.promotion_id == promotion_row.id).order_by(CheckResultTable.name)).all()
        override_rows = session.scalars(select(CheckOverrideTable).where(CheckOverrideTable.promotion_id == promotion_row.id)).all()
        promotion_row.required_checks = [
            {
                "name": check_row.name,
                "state": "overridden" if any(override.check_result_id == check_row.id and override.state == "approved" for override in override_rows) else check_row.state,
                "detail": check_row.detail,
            }
            for check_row in check_rows
        ]

    @staticmethod
    def promotion_ready(check_rows, override_rows, approvals: list[dict]) -> bool:
        return all(
            check.state == "passed" or any(override.check_result_id == check.id and override.state == "approved" for override in override_rows)
            for check in check_rows
        ) and all(approval["state"] == "approved" for approval in approvals)

    @classmethod
    def promotion_readiness(cls, check_rows, override_rows, approvals: list[dict]) -> str:
        if cls.promotion_ready(check_rows, override_rows, approvals):
            return "Approved for promotion execution."
        pending_checks = sum(
            1
            for check in check_rows
            if check.state != "passed" and not any(override.check_result_id == check.id and override.state == "approved" for override in override_rows)
        )
        pending_approvals = sum(1 for approval in approvals if approval["state"] != "approved")
        return f"Blocked until {pending_checks} checks and {pending_approvals} approvals are satisfied."

    @classmethod
    def promotion_readiness_from_db(cls, session, promotion_row: PromotionTable) -> str:
        check_rows = session.scalars(select(CheckResultTable).where(CheckResultTable.promotion_id == promotion_row.id)).all()
        override_rows = session.scalars(select(CheckOverrideTable).where(CheckOverrideTable.promotion_id == promotion_row.id)).all()
        return cls.promotion_readiness(check_rows, override_rows, promotion_row.required_approvals)

    @classmethod
    def run_promotion_checks(cls, session, request_row: RequestTable | RequestRecord, promotion_row: PromotionTable, actor_id: str) -> None:
        cls.ensure_promotion_check_records(session, promotion_row, actor_id)
        artifact_row = session.scalars(select(ArtifactTable).where(ArtifactTable.request_id == request_row.id).order_by(desc(ArtifactTable.updated_at))).first()
        review_row = session.scalars(select(ReviewQueueTable).where(ReviewQueueTable.request_id == request_row.id).order_by(desc(ReviewQueueTable.id))).first()
        check_rows = session.scalars(select(CheckResultTable).where(CheckResultTable.promotion_id == promotion_row.id)).all()
        now = datetime.now(timezone.utc)
        for check_row in check_rows:
            if check_row.name == "Policy Bundle":
                passed = request_row.policy_context.get("policy_bundle_passed", True) is not False
                check_row.state = "passed" if passed else "failed"
                check_row.detail = "Automated policy bundle evaluation passed." if passed else "Automated policy bundle evaluation failed."
                check_row.evidence = f"policy_context={request_row.policy_context}"
            elif check_row.name == "Approval Freshness":
                fresh = artifact_row is not None and not artifact_row.stale_review and (review_row is None or review_row.blocking_status == "Approved")
                check_row.state = "passed" if fresh else "pending"
                check_row.detail = "Latest approved artifact is fresh." if fresh else "Waiting for fresh approval evidence."
                check_row.evidence = f"artifact_stale={artifact_row.stale_review if artifact_row else 'missing'}, review_state={review_row.blocking_status if review_row else 'missing'}"
            check_row.evaluated_at = now
            check_row.evaluated_by = actor_id
        cls.sync_promotion_checks(session, promotion_row)


policy_check_service = PolicyCheckService()
