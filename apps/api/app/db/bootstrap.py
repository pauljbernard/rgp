from sqlalchemy import inspect, select
from sqlalchemy import func

from app.db.base import Base
from app.db.models import ArtifactTable, CapabilityTable, CheckOverrideTable, CheckResultTable, IntegrationTable, OrganizationTable, PolicyTable, PortfolioScopeTable, PortfolioTable, PromotionTable, RequestEventTable, RequestTable, ReviewQueueTable, RunTable, TeamMembershipTable, TeamTable, TemplateTable, TenantTable, TransitionGateTable, UserTable
from app.db.session import SessionLocal, engine
from app.models.governance import seed_artifacts, seed_audit_entries, seed_capabilities, seed_integrations, seed_policies, seed_promotions, seed_requests, seed_review_queue, seed_runs, seed_templates


def _as_datetime(value):
    if hasattr(value, "tzinfo"):
        return value
    return value and __import__("datetime").datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def initialize_database() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "alembic_version" not in table_names and "requests" not in table_names:
        Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        has_requests = session.scalar(select(func.count()).select_from(RequestTable)) if "requests" in set(inspector.get_table_names()) else 0
        if not has_requests:
            for request in seed_requests():
                session.add(
                    RequestTable(
                        **request.model_dump(mode="python"),
                    )
                )

        if "templates" in set(inspector.get_table_names()):
            existing_templates = {
                (row.id, row.version)
                for row in session.scalars(select(TemplateTable)).all()
            }
            for template in seed_templates():
                if (template.id, template.version) in existing_templates:
                    continue
                payload = template.model_dump(mode="python", by_alias=False)
                payload["tenant_id"] = "tenant_demo"
                payload["template_schema"] = payload.pop("template_schema")
                payload["created_at"] = _as_datetime(payload["created_at"])
                payload["updated_at"] = _as_datetime(payload["updated_at"])
                session.add(TemplateTable(**payload))

        if "users" in set(inspector.get_table_names()):
            now = _as_datetime("2026-03-31T00:00:00+00:00")
            if "tenants" in set(inspector.get_table_names()):
                existing_tenant_ids = set(session.scalars(select(TenantTable.id)).all())
                for tenant in [
                    ("tenant_demo", "Demo Tenant"),
                    ("tenant_other", "Other Tenant"),
                ]:
                    if tenant[0] in existing_tenant_ids:
                        continue
                    session.add(
                        TenantTable(
                            id=tenant[0],
                            name=tenant[1],
                            status="active",
                            created_at=now,
                            updated_at=now,
                        )
                    )
            existing_user_ids = set(session.scalars(select(UserTable.id)).all())
            for user in [
                ("user_demo", "Demo User", "demo@rgp.local", ["platform_admin", "operator", "reviewer", "submitter"]),
                ("reviewer_nina", "Nina Reviewer", "nina@rgp.local", ["reviewer"]),
                ("reviewer_liam", "Liam Reviewer", "liam@rgp.local", ["reviewer"]),
                ("ops_isaac", "Isaac Ops", "isaac@rgp.local", ["operator"]),
                ("ops_override", "Override Ops", "override.ops@rgp.local", ["operator"]),
                ("reviewer_override", "Override Reviewer", "override.reviewer@rgp.local", ["reviewer"]),
                ("tenant_admin_demo", "Demo Tenant Admin", "tenant.admin@rgp.local", ["tenant_admin", "operator", "reviewer", "submitter"]),
            ]:
                if user[0] in existing_user_ids:
                    continue
                session.add(
                    UserTable(
                        id=user[0],
                        tenant_id="tenant_demo",
                        display_name=user[1],
                        email=user[2],
                        role_summary=user[3],
                        status="active",
                        created_at=now,
                        updated_at=now,
                    )
                )

        if "teams" in set(inspector.get_table_names()):
            now = _as_datetime("2026-03-31T00:00:00+00:00")
            if "organizations" in set(inspector.get_table_names()):
                existing_organization_ids = set(session.scalars(select(OrganizationTable.id)).all())
                for organization in [
                    ("org_curriculum", "tenant_demo", "Curriculum Programs"),
                    ("org_assessment", "tenant_demo", "Assessment and Quality"),
                    ("org_operations", "tenant_demo", "Platform Operations"),
                    ("org_other_delivery", "tenant_other", "Other Tenant Delivery"),
                ]:
                    if organization[0] in existing_organization_ids:
                        continue
                    session.add(
                        OrganizationTable(
                            id=organization[0],
                            tenant_id=organization[1],
                            name=organization[2],
                            status="active",
                            created_at=now,
                            updated_at=now,
                        )
                    )
            existing_team_ids = set(session.scalars(select(TeamTable.id)).all())
            for team in [
                ("team_curriculum_science", "tenant_demo", "org_curriculum", "Curriculum Science", "delivery"),
                ("team_curriculum", "tenant_demo", "org_curriculum", "Curriculum Core", "delivery"),
                ("team_assessment_quality", "tenant_demo", "org_assessment", "Assessment Quality", "delivery"),
                ("team_assessment", "tenant_demo", "org_assessment", "Assessment Delivery", "delivery"),
                ("team_science", "tenant_demo", "org_curriculum", "Science Delivery", "delivery"),
                ("team_literacy", "tenant_demo", "org_curriculum", "Literacy Delivery", "delivery"),
                ("team_ops", "tenant_demo", "org_operations", "Platform Operations", "operations"),
                ("team_other_ops", "tenant_other", "org_other_delivery", "Other Tenant Operations", "operations"),
            ]:
                if team[0] in existing_team_ids:
                    if hasattr(TeamTable, "organization_id"):
                        row = session.get(TeamTable, team[0])
                        if row is not None and not getattr(row, "organization_id", None):
                            row.organization_id = team[2]
                            row.updated_at = now
                    continue
                session.add(
                    TeamTable(
                        id=team[0],
                        tenant_id=team[1],
                        organization_id=team[2],
                        name=team[3],
                        kind=team[4],
                        status="active",
                        created_at=now,
                        updated_at=now,
                    )
                )

        if "team_memberships" in set(inspector.get_table_names()):
            now = _as_datetime("2026-03-31T00:00:00+00:00")
            existing_membership_ids = set(session.scalars(select(TeamMembershipTable.id)).all())
            for membership in [
                ("tm_001", "team_curriculum_science", "reviewer_nina", "reviewer"),
                ("tm_002", "team_curriculum_science", "reviewer_liam", "reviewer"),
                ("tm_003", "team_ops", "ops_isaac", "approver"),
                ("tm_004", "team_ops", "ops_override", "approver"),
                ("tm_005", "team_curriculum", "user_demo", "lead"),
                ("tm_006", "team_assessment", "user_demo", "lead"),
                ("tm_007", "team_science", "reviewer_nina", "reviewer"),
                ("tm_008", "team_literacy", "reviewer_liam", "reviewer"),
                ("tm_009", "team_ops", "tenant_admin_demo", "lead"),
            ]:
                if membership[0] in existing_membership_ids:
                    continue
                session.add(
                    TeamMembershipTable(
                        id=membership[0],
                        tenant_id="tenant_demo",
                        team_id=membership[1],
                        user_id=membership[2],
                        role=membership[3],
                        created_at=now,
                    )
                )

        if "portfolios" in set(inspector.get_table_names()):
            now = _as_datetime("2026-03-31T00:00:00+00:00")
            existing_portfolio_ids = set(session.scalars(select(PortfolioTable.id)).all())
            for portfolio in [
                ("port_curriculum", "Curriculum Delivery", "team_curriculum"),
                ("port_quality", "Assessment Quality", "team_assessment_quality"),
            ]:
                if portfolio[0] in existing_portfolio_ids:
                    continue
                session.add(
                    PortfolioTable(
                        id=portfolio[0],
                        tenant_id="tenant_demo",
                        name=portfolio[1],
                        status="active",
                        owner_team_id=portfolio[2],
                        created_at=now,
                        updated_at=now,
                    )
                )

        if "portfolio_scopes" in set(inspector.get_table_names()):
            existing_scope_ids = set(session.scalars(select(PortfolioScopeTable.id)).all())
            for scope in [
                ("ps_001", "port_curriculum", "team", "team_curriculum_science"),
                ("ps_002", "port_curriculum", "team", "team_curriculum"),
                ("ps_003", "port_quality", "team", "team_assessment_quality"),
                ("ps_004", "port_quality", "team", "team_assessment"),
            ]:
                if scope[0] in existing_scope_ids:
                    continue
                session.add(
                    PortfolioScopeTable(
                        id=scope[0],
                        tenant_id="tenant_demo",
                        portfolio_id=scope[1],
                        scope_type=scope[2],
                        scope_key=scope[3],
                    )
                )

        has_runs = session.scalar(select(func.count()).select_from(RunTable)) if "runs" in set(inspector.get_table_names()) else 0
        if not has_runs:
            for run in seed_runs():
                payload = run.model_dump(mode="python")
                session.add(
                    RunTable(
                        id=payload["id"],
                        request_id=payload["request_id"],
                        workflow=payload["workflow"],
                        status=payload["status"],
                        current_step=payload["current_step"],
                        elapsed_time=payload["elapsed_time"],
                        waiting_reason=payload.get("waiting_reason"),
                        updated_at=_as_datetime(payload["updated_at"]),
                        owner_team=payload["owner_team"],
                        workflow_identity=payload["workflow_identity"],
                        progress_percent=payload["progress_percent"],
                        current_step_input_summary=payload["current_step_input_summary"],
                        current_step_output_summary=payload["current_step_output_summary"],
                        failure_reason=payload.get("failure_reason"),
                        command_surface=payload["command_surface"],
                        steps=[step.model_dump(mode="python") for step in run.steps],
                        run_context=[[label, value] for label, value in run.run_context],
                        conversation_thread_id=payload["conversation_thread_id"],
                    )
                )

        has_artifacts = session.scalar(select(func.count()).select_from(ArtifactTable)) if "artifacts" in set(inspector.get_table_names()) else 0
        if not has_artifacts:
            for artifact in seed_artifacts():
                payload = artifact.model_dump(mode="python")
                artifact_payload = payload["artifact"]
                session.add(
                    ArtifactTable(
                        id=artifact_payload["id"],
                        type=artifact_payload["type"],
                        name=artifact_payload["name"],
                        current_version=artifact_payload["current_version"],
                        status=artifact_payload["status"],
                        request_id=artifact_payload["request_id"],
                        updated_at=_as_datetime(artifact_payload["updated_at"]),
                        owner=artifact_payload["owner"],
                        review_state=artifact_payload["review_state"],
                        promotion_relevant=artifact_payload["promotion_relevant"],
                        versions=payload["versions"],
                        selected_version_id=payload["selected_version_id"],
                        stale_review=payload["stale_review"],
                    )
                )

        has_review_queue = session.scalar(select(func.count()).select_from(ReviewQueueTable)) if "review_queue" in set(inspector.get_table_names()) else 0
        if not has_review_queue:
            for item in seed_review_queue():
                session.add(ReviewQueueTable(**item.model_dump(mode="python")))

        has_promotions = session.scalar(select(func.count()).select_from(PromotionTable)) if "promotions" in set(inspector.get_table_names()) else 0
        if not has_promotions:
            for promotion in seed_promotions():
                payload = promotion.model_dump(mode="python")
                session.add(
                    PromotionTable(
                        id=payload["id"],
                        request_id=payload["request_id"],
                        target=payload["target"],
                        strategy=payload["strategy"],
                        required_checks=payload["required_checks"],
                        required_approvals=payload["required_approvals"],
                        stale_warnings=payload["stale_warnings"],
                        execution_readiness=payload["execution_readiness"],
                        promotion_history=payload["promotion_history"],
                    )
                )

        has_check_results = session.scalar(select(func.count()).select_from(CheckResultTable)) if "check_results" in set(inspector.get_table_names()) else 0
        if not has_check_results:
            for promotion in session.scalars(select(PromotionTable)).all():
                for index, check in enumerate(promotion.required_checks, start=1):
                    session.add(
                        CheckResultTable(
                            id=f"chk_{promotion.id}_{index}",
                            request_id=promotion.request_id,
                            promotion_id=promotion.id,
                            name=check["name"],
                            state=check["state"],
                            detail=check["detail"],
                            severity="required",
                            evidence="Seeded promotion gate check",
                            evaluated_at=_as_datetime("2026-03-30T00:00:00+00:00"),
                            evaluated_by="seed",
                        )
                    )

        has_check_overrides = session.scalar(select(func.count()).select_from(CheckOverrideTable)) if "check_overrides" in set(inspector.get_table_names()) else 0
        if not has_check_overrides:
            pass

        has_capabilities = session.scalar(select(func.count()).select_from(CapabilityTable)) if "capabilities" in set(inspector.get_table_names()) else 0
        if not has_capabilities:
            for capability in seed_capabilities():
                payload = capability.model_dump(mode="python")
                capability_payload = payload["capability"]
                session.add(
                    CapabilityTable(
                        id=capability_payload["id"],
                        tenant_id="tenant_demo",
                        name=capability_payload["name"],
                        type=capability_payload["type"],
                        version=capability_payload["version"],
                        status=capability_payload["status"],
                        owner=capability_payload["owner"],
                        updated_at=_as_datetime(capability_payload["updated_at"]),
                        usage_count=capability_payload["usage_count"],
                        definition=payload["definition"],
                        lineage=payload["lineage"],
                        usage=payload["usage"],
                        performance=payload["performance"],
                        history=payload["history"],
                    )
                )

        has_policies = session.scalar(select(func.count()).select_from(PolicyTable)) if "policies" in set(inspector.get_table_names()) else 0
        if not has_policies:
            for policy in seed_policies():
                payload = policy.model_dump(mode="python")
                session.add(
                    PolicyTable(
                        id=payload["id"],
                        tenant_id="tenant_demo",
                        name=payload["name"],
                        status=payload["status"],
                        scope=payload["scope"],
                        updated_at=_as_datetime(payload["updated_at"]),
                    )
                )

        has_transition_gates = session.scalar(select(func.count()).select_from(TransitionGateTable)) if "transition_gates" in set(inspector.get_table_names()) else 0
        if not has_transition_gates:
            for gate in [
                ("tg_001", "pol_001", "request", "validated", "Intake Completeness", 1),
                ("tg_002", "pol_001", "request", "approved", "Review Package Readiness", 1),
                ("tg_003", "pol_001", "request", "promotion_pending", "Intake Completeness", 1),
                ("tg_004", "pol_001", "request", "promotion_pending", "Review Package Readiness", 2),
                ("tg_005", "pol_001", "request", "promotion_pending", "Approval Freshness", 3),
            ]:
                session.add(
                    TransitionGateTable(
                        id=gate[0],
                        tenant_id="tenant_demo",
                        policy_id=gate[1],
                        gate_scope=gate[2],
                        transition_target=gate[3],
                        required_check_name=gate[4],
                        gate_order=gate[5],
                        active=True,
                    )
                )

        if "integrations" in set(inspector.get_table_names()):
            existing_integration_ids = set(session.scalars(select(IntegrationTable.id)).all())
            for integration in seed_integrations():
                payload = integration.model_dump(mode="python")
                if payload["id"] in existing_integration_ids:
                    continue
                session.add(
                    IntegrationTable(
                        id=payload["id"],
                        tenant_id="tenant_demo",
                        name=payload["name"],
                        type=payload["type"],
                        status=payload["status"],
                        endpoint=payload["endpoint"],
                        settings=payload.get("settings", {}),
                    )
                )

        has_events = session.scalar(select(func.count()).select_from(RequestEventTable)) if "request_events" in set(inspector.get_table_names()) else 0
        if not has_events:
            for event in seed_audit_entries():
                session.add(
                    RequestEventTable(
                        request_id=event.object_id if event.object_type == "request" else "req_001",
                        timestamp=_as_datetime(event.timestamp),
                        actor=event.actor,
                        action=event.action,
                        object_type=event.object_type,
                        object_id=event.object_id,
                        reason_or_evidence=event.reason_or_evidence,
                    )
                )

        session.commit()
