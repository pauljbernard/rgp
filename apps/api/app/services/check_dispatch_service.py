from datetime import datetime, timezone
import threading
import time

from celery import Celery
from sqlalchemy import desc, select

from app.core.config import settings
from app.db.models import CheckRunTable, PromotionTable, RequestEventTable, RequestTable
from app.db.session import SessionLocal
from app.models.governance import CheckRunStatus
from app.services.event_store_service import event_store_service
from app.services.policy_check_service import policy_check_service
from app.services.request_state_bridge import get_request_state, record_request_event


celery_dispatch_app = Celery("rgp-check-dispatch", broker=settings.redis_url, backend=settings.redis_url)


class CheckDispatchService:
    def __init__(self) -> None:
        self._local_lock = threading.Lock()
        self._local_inflight: set[str] = set()

    def enqueue_request_checks(self, session, request_id: str, actor_id: str, reason: str) -> CheckRunTable:
        existing = session.scalars(
            select(CheckRunTable)
            .where(
                CheckRunTable.request_id == request_id,
                CheckRunTable.promotion_id.is_(None),
                CheckRunTable.scope == "request",
                CheckRunTable.status.in_([CheckRunStatus.QUEUED.value, CheckRunStatus.RUNNING.value]),
            )
            .order_by(desc(CheckRunTable.queued_at))
        ).first()
        if existing is not None:
            return existing
        check_run = CheckRunTable(
            id=self._next_check_run_id(session),
            request_id=request_id,
            promotion_id=None,
            scope="request",
            status=CheckRunStatus.QUEUED.value,
            trigger_reason=reason,
            enqueued_by=actor_id,
            worker_task_id=None,
            error_message=None,
            queued_at=datetime.now(timezone.utc),
            started_at=None,
            completed_at=None,
        )
        session.add(check_run)
        session.flush()
        request_tenant_id = self._request_tenant_id(session, request_id)
        event_store_service.append(
            session,
            tenant_id=request_tenant_id,
            event_type="check_run.enqueued",
            aggregate_type="check_run",
            aggregate_id=check_run.id,
            request_id=request_id,
            check_run_id=check_run.id,
            actor=actor_id,
            detail=reason,
            payload={"scope": "request"},
        )
        self._dispatch(session, check_run.id)
        return check_run

    def enqueue_promotion_checks(self, session, promotion_id: str, request_id: str, actor_id: str, reason: str) -> CheckRunTable:
        existing = session.scalars(
            select(CheckRunTable)
            .where(
                CheckRunTable.promotion_id == promotion_id,
                CheckRunTable.scope == "promotion",
                CheckRunTable.status.in_([CheckRunStatus.QUEUED.value, CheckRunStatus.RUNNING.value]),
            )
            .order_by(desc(CheckRunTable.queued_at))
        ).first()
        if existing is not None:
            return existing
        check_run = CheckRunTable(
            id=self._next_check_run_id(session),
            request_id=request_id,
            promotion_id=promotion_id,
            scope="promotion",
            status=CheckRunStatus.QUEUED.value,
            trigger_reason=reason,
            enqueued_by=actor_id,
            worker_task_id=None,
            error_message=None,
            queued_at=datetime.now(timezone.utc),
            started_at=None,
            completed_at=None,
        )
        session.add(check_run)
        session.flush()
        request_tenant_id = self._request_tenant_id(session, request_id)
        event_store_service.append(
            session,
            tenant_id=request_tenant_id,
            event_type="check_run.enqueued",
            aggregate_type="check_run",
            aggregate_id=check_run.id,
            request_id=request_id,
            promotion_id=promotion_id,
            check_run_id=check_run.id,
            actor=actor_id,
            detail=reason,
            payload={"scope": "promotion"},
        )
        self._dispatch(session, check_run.id)
        return check_run

    @staticmethod
    def has_pending_request_check_run(session, request_id: str) -> bool:
        return (
            session.scalars(
                select(CheckRunTable).where(
                    CheckRunTable.request_id == request_id,
                    CheckRunTable.scope == "request",
                    CheckRunTable.status.in_([CheckRunStatus.QUEUED.value, CheckRunStatus.RUNNING.value]),
                )
            ).first()
            is not None
        )

    @staticmethod
    def has_pending_promotion_check_run(session, promotion_id: str) -> bool:
        return (
            session.scalars(
                select(CheckRunTable).where(
                    CheckRunTable.promotion_id == promotion_id,
                    CheckRunTable.scope == "promotion",
                    CheckRunTable.status.in_([CheckRunStatus.QUEUED.value, CheckRunStatus.RUNNING.value]),
                )
            ).first()
            is not None
        )

    @staticmethod
    def _request_tenant_id(session, request_id: str) -> str:
        request_row = session.get(RequestTable, request_id)
        if request_row is not None:
            return request_row.tenant_id
        request_state = get_request_state(request_id, None)
        if request_state is not None:
            return request_state.tenant_id
        raise StopIteration(request_id)

    def execute_check_run(self, check_run_id: str) -> None:
        with SessionLocal() as session:
            check_run = session.get(CheckRunTable, check_run_id)
            if check_run is None:
                raise StopIteration(check_run_id)
            if check_run.status == CheckRunStatus.COMPLETED.value:
                return
            check_run.status = CheckRunStatus.RUNNING.value
            check_run.started_at = datetime.now(timezone.utc)
            check_run.error_message = None
            request_row = session.get(RequestTable, check_run.request_id)
            request_state = request_row or get_request_state(check_run.request_id, None)
            if request_state is None:
                raise StopIteration(check_run.request_id)
            tenant_id = request_row.tenant_id if request_row is not None else request_state.tenant_id
            dynamodb_adapter = None
            if request_row is None and check_run.scope == "request":
                from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

                dynamodb_adapter = DynamoDbGovernancePersistenceAdapter()
                dynamodb_adapter._update_request_check_run_item(
                    check_run.id,
                    status=CheckRunStatus.RUNNING.value,
                    worker_task_id=check_run.worker_task_id,
                    started_at=check_run.started_at.isoformat().replace("+00:00", "Z") if check_run.started_at else None,
                )
            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="check_run.started",
                aggregate_type="check_run",
                aggregate_id=check_run.id,
                request_id=check_run.request_id,
                promotion_id=check_run.promotion_id,
                check_run_id=check_run.id,
                actor=check_run.enqueued_by,
                detail=check_run.trigger_reason,
                payload={"scope": check_run.scope},
            )
            session.flush()
            try:
                if check_run.scope == "request":
                    policy_check_service.run_request_checks(session, request_state, check_run.enqueued_by)
                    if request_row is not None:
                        session.add(
                            RequestEventTable(
                                request_id=request_row.id,
                                timestamp=datetime.now(timezone.utc),
                                actor=check_run.enqueued_by,
                                action="Request Checks Executed",
                                object_type="request",
                                object_id=request_row.id,
                                reason_or_evidence=check_run.trigger_reason,
                            )
                        )
                elif check_run.scope == "promotion":
                    promotion_row = session.get(PromotionTable, check_run.promotion_id)
                    if promotion_row is None:
                        raise StopIteration(check_run.promotion_id)
                    policy_check_service.run_promotion_checks(session, request_state, promotion_row, check_run.enqueued_by)
                    promotion_row.execution_readiness = policy_check_service.promotion_readiness_from_db(session, promotion_row)
                    history = list(promotion_row.promotion_history)
                    history.append(
                        {
                            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                            "actor": check_run.enqueued_by,
                            "action": "Automated checks executed",
                        }
                    )
                    promotion_row.promotion_history = history
                else:
                    raise ValueError(f"Unsupported check run scope {check_run.scope}")
                check_run.status = CheckRunStatus.COMPLETED.value
                check_run.completed_at = datetime.now(timezone.utc)
                event_store_service.append(
                    session,
                    tenant_id=tenant_id,
                    event_type="check_run.completed",
                    aggregate_type="check_run",
                    aggregate_id=check_run.id,
                    request_id=check_run.request_id,
                    promotion_id=check_run.promotion_id,
                    check_run_id=check_run.id,
                    actor=check_run.enqueued_by,
                    detail=check_run.trigger_reason,
                    payload={"scope": check_run.scope},
                )
                session.commit()
                if dynamodb_adapter is not None:
                    dynamodb_adapter._update_request_check_run_item(
                        check_run.id,
                        status=CheckRunStatus.COMPLETED.value,
                        worker_task_id=check_run.worker_task_id,
                        started_at=check_run.started_at.isoformat().replace("+00:00", "Z") if check_run.started_at else None,
                        completed_at=check_run.completed_at.isoformat().replace("+00:00", "Z"),
                    )
                if request_row is None and check_run.scope == "request":
                    record_request_event(
                        check_run.request_id,
                        tenant_id,
                        check_run.enqueued_by,
                        "Request Checks Executed",
                        check_run.trigger_reason,
                    )
            except Exception as exc:
                session.rollback()
                failed = session.get(CheckRunTable, check_run_id)
                request_row = session.get(RequestTable, check_run.request_id)
                request_state = request_row or get_request_state(check_run.request_id, None)
                if failed is not None:
                    failed.status = CheckRunStatus.FAILED.value
                    failed.error_message = str(exc)
                    failed.completed_at = datetime.now(timezone.utc)
                    if request_state is not None:
                        event_store_service.append(
                            session,
                            tenant_id=request_row.tenant_id if request_row is not None else request_state.tenant_id,
                            event_type="check_run.failed",
                            aggregate_type="check_run",
                            aggregate_id=failed.id,
                            request_id=failed.request_id,
                            promotion_id=failed.promotion_id,
                            check_run_id=failed.id,
                            actor=failed.enqueued_by,
                            detail=str(exc),
                            payload={"scope": failed.scope},
                        )
                    session.commit()
                    if request_state is not None and request_row is None and failed.scope == "request":
                        from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

                        DynamoDbGovernancePersistenceAdapter()._update_request_check_run_item(
                            failed.id,
                            status=CheckRunStatus.FAILED.value,
                            worker_task_id=failed.worker_task_id,
                            error_message=str(exc),
                            started_at=failed.started_at.isoformat().replace("+00:00", "Z") if failed.started_at else None,
                            completed_at=failed.completed_at.isoformat().replace("+00:00", "Z") if failed.completed_at else None,
                        )
                raise

    def _dispatch(self, session, check_run_id: str) -> None:
        check_run = session.get(CheckRunTable, check_run_id)
        if check_run is None:
            return
        if settings.check_dispatch_backend.lower() == "local":
            check_run.worker_task_id = f"local:{check_run_id}"
            session.flush()
            self._dispatch_local(check_run_id)
            return
        try:
            result = celery_dispatch_app.send_task("rgp.run_check_run", args=[check_run_id])
            check_run.worker_task_id = result.id
            session.flush()
        except Exception as exc:
            raise ValueError(f"Check dispatch failed: {exc}") from exc

    def _dispatch_local(self, check_run_id: str) -> None:
        with self._local_lock:
            if check_run_id in self._local_inflight:
                return
            self._local_inflight.add(check_run_id)

        def _runner() -> None:
            try:
                for _ in range(20):
                    try:
                        self.execute_check_run(check_run_id)
                        return
                    except StopIteration:
                        time.sleep(0.1)
            finally:
                with self._local_lock:
                    self._local_inflight.discard(check_run_id)

        threading.Thread(target=_runner, name=f"rgp-check-{check_run_id}", daemon=True).start()

    @staticmethod
    def _next_check_run_id(session) -> str:
        existing_ids = session.scalars(select(CheckRunTable.id)).all()
        numeric_suffixes = []
        for identifier in existing_ids:
            parts = identifier.split("_", 1)
            if len(parts) != 2 or not parts[1].isdigit():
                continue
            numeric_suffixes.append(int(parts[1]))
        next_number = max(numeric_suffixes, default=0) + 1
        return f"cr_{next_number:03d}"


check_dispatch_service = CheckDispatchService()
