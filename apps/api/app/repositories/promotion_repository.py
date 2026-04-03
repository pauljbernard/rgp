"""Promotion and review repository — owns promotion, review queue, and check orchestration.

Delegates to governance_repository for now; the actual method implementations
will be migrated here incrementally as the monolith is decomposed.
"""

from __future__ import annotations

from app.models.common import PaginatedResponse
from app.models.governance import (
    CheckEvaluationRequest,
    CheckOverrideRequest,
    CheckRunRecord,
    CheckRunRequest,
    PromotionActionRequest,
    PromotionApprovalOverrideRequest,
    PromotionDetail,
    ReviewAssignmentOverrideRequest,
    ReviewDecisionRequest,
    ReviewQueueItem,
)
from app.repositories.governance_repository import governance_repository


class PromotionRepository:
    """Encapsulates all promotion, review, and check operations."""

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
        return governance_repository.list_review_queue(page, page_size, assigned_reviewer, blocking_only, stale_only, request_id, tenant_id)

    def get_promotion(self, promotion_id: str, tenant_id: str | None = None) -> PromotionDetail:
        return governance_repository.get_promotion(promotion_id, tenant_id)

    def record_review_decision(self, review_id: str, payload: ReviewDecisionRequest, tenant_id: str) -> ReviewQueueItem:
        return governance_repository.record_review_decision(review_id, payload, tenant_id)

    def override_review_assignment(self, review_id: str, payload: ReviewAssignmentOverrideRequest, tenant_id: str) -> ReviewQueueItem:
        return governance_repository.override_review_assignment(review_id, payload, tenant_id)

    def apply_promotion_action(self, promotion_id: str, payload: PromotionActionRequest, tenant_id: str) -> PromotionDetail:
        return governance_repository.apply_promotion_action(promotion_id, payload, tenant_id)

    def evaluate_check(self, promotion_id: str, check_id: str, payload: CheckEvaluationRequest, tenant_id: str) -> PromotionDetail:
        return governance_repository.evaluate_check(promotion_id, check_id, payload, tenant_id)

    def override_check(self, promotion_id: str, check_id: str, payload: CheckOverrideRequest, tenant_id: str) -> PromotionDetail:
        return governance_repository.override_check(promotion_id, check_id, payload, tenant_id)

    def run_promotion_checks(self, promotion_id: str, payload: CheckRunRequest, tenant_id: str) -> PromotionDetail:
        return governance_repository.run_promotion_checks(promotion_id, payload, tenant_id)

    def override_promotion_approval(self, promotion_id: str, payload: PromotionApprovalOverrideRequest, tenant_id: str) -> PromotionDetail:
        return governance_repository.override_promotion_approval(promotion_id, payload, tenant_id)

    def list_request_check_runs(self, request_id: str, tenant_id: str | None = None) -> list[CheckRunRecord]:
        return governance_repository.list_request_check_runs(request_id, tenant_id)

    def list_promotion_check_runs(self, promotion_id: str, tenant_id: str | None = None) -> list[CheckRunRecord]:
        return governance_repository.list_promotion_check_runs(promotion_id, tenant_id)


promotion_repository = PromotionRepository()
