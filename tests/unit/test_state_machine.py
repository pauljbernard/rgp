"""Unit tests for the extracted state machine module."""

import unittest
from datetime import datetime, timedelta, timezone

from app.domain.state_machine import (
    AMENDABLE_STATUSES,
    CANCELABLE_STATUSES,
    SUBMITTABLE_STATUSES,
    TRANSITION_RULES,
    SLA_POLICY_RULES,
    allowed_transitions,
    assert_amendable,
    assert_cancelable,
    assert_submittable,
    assert_valid_transition,
    compute_sla_risk,
    is_valid_transition,
)
from app.models.request import RequestStatus


class TransitionRulesTest(unittest.TestCase):
    """Verify TRANSITION_RULES constants match the governance specification."""

    def test_submitted_can_reach_validated_or_validation_failed_or_canceled(self) -> None:
        expected = {RequestStatus.VALIDATED, RequestStatus.VALIDATION_FAILED, RequestStatus.CANCELED}
        self.assertEqual(TRANSITION_RULES[RequestStatus.SUBMITTED], expected)

    def test_promoted_can_only_reach_completed(self) -> None:
        self.assertEqual(TRANSITION_RULES[RequestStatus.PROMOTED], {RequestStatus.COMPLETED})

    def test_failed_can_reach_planned_or_canceled(self) -> None:
        self.assertEqual(TRANSITION_RULES[RequestStatus.FAILED], {RequestStatus.PLANNED, RequestStatus.CANCELED})

    def test_all_governed_statuses_have_rules(self) -> None:
        governed = {
            RequestStatus.SUBMITTED,
            RequestStatus.VALIDATION_FAILED,
            RequestStatus.VALIDATED,
            RequestStatus.CLASSIFIED,
            RequestStatus.OWNERSHIP_RESOLVED,
            RequestStatus.PLANNED,
            RequestStatus.QUEUED,
            RequestStatus.IN_EXECUTION,
            RequestStatus.AWAITING_INPUT,
            RequestStatus.AWAITING_REVIEW,
            RequestStatus.UNDER_REVIEW,
            RequestStatus.CHANGES_REQUESTED,
            RequestStatus.APPROVED,
            RequestStatus.PROMOTION_PENDING,
            RequestStatus.PROMOTED,
            RequestStatus.FAILED,
        }
        self.assertEqual(set(TRANSITION_RULES.keys()), governed)

    def test_draft_has_no_transition_rules(self) -> None:
        self.assertNotIn(RequestStatus.DRAFT, TRANSITION_RULES)

    def test_completed_has_no_transition_rules(self) -> None:
        self.assertNotIn(RequestStatus.COMPLETED, TRANSITION_RULES)

    def test_canceled_has_no_transition_rules(self) -> None:
        self.assertNotIn(RequestStatus.CANCELED, TRANSITION_RULES)


class IsValidTransitionTest(unittest.TestCase):
    def test_valid_forward_transition(self) -> None:
        self.assertTrue(is_valid_transition(RequestStatus.SUBMITTED, RequestStatus.VALIDATED))

    def test_invalid_backward_transition(self) -> None:
        self.assertFalse(is_valid_transition(RequestStatus.VALIDATED, RequestStatus.SUBMITTED))

    def test_cancel_is_always_valid_from_cancelable(self) -> None:
        for status in CANCELABLE_STATUSES:
            if status in TRANSITION_RULES:
                self.assertTrue(
                    is_valid_transition(status, RequestStatus.CANCELED),
                    f"Cancel from {status} should be valid",
                )

    def test_transition_from_terminal_status(self) -> None:
        self.assertFalse(is_valid_transition(RequestStatus.COMPLETED, RequestStatus.DRAFT))
        self.assertFalse(is_valid_transition(RequestStatus.CANCELED, RequestStatus.DRAFT))


class AllowedTransitionsTest(unittest.TestCase):
    def test_returns_empty_for_terminal(self) -> None:
        self.assertEqual(allowed_transitions(RequestStatus.COMPLETED), set())

    def test_returns_correct_set(self) -> None:
        result = allowed_transitions(RequestStatus.APPROVED)
        self.assertEqual(result, {RequestStatus.PROMOTION_PENDING, RequestStatus.COMPLETED, RequestStatus.CANCELED})


class AssertionHelpersTest(unittest.TestCase):
    def test_assert_submittable_raises_on_invalid(self) -> None:
        with self.assertRaises(ValueError):
            assert_submittable(RequestStatus.COMPLETED)

    def test_assert_submittable_passes_on_draft(self) -> None:
        assert_submittable(RequestStatus.DRAFT)

    def test_assert_amendable_raises_on_completed(self) -> None:
        with self.assertRaises(ValueError):
            assert_amendable(RequestStatus.COMPLETED)

    def test_assert_amendable_passes_on_draft(self) -> None:
        assert_amendable(RequestStatus.DRAFT)

    def test_assert_cancelable_raises_on_completed(self) -> None:
        with self.assertRaises(ValueError):
            assert_cancelable(RequestStatus.COMPLETED)

    def test_assert_cancelable_passes_on_in_execution(self) -> None:
        assert_cancelable(RequestStatus.IN_EXECUTION)

    def test_assert_valid_transition_raises(self) -> None:
        with self.assertRaises(ValueError):
            assert_valid_transition(RequestStatus.COMPLETED, RequestStatus.DRAFT)

    def test_assert_valid_transition_passes(self) -> None:
        assert_valid_transition(RequestStatus.SUBMITTED, RequestStatus.VALIDATED)


class StatusSetsTest(unittest.TestCase):
    def test_submittable_includes_draft(self) -> None:
        self.assertIn(RequestStatus.DRAFT, SUBMITTABLE_STATUSES)

    def test_submittable_excludes_completed(self) -> None:
        self.assertNotIn(RequestStatus.COMPLETED, SUBMITTABLE_STATUSES)

    def test_amendable_includes_most_active_statuses(self) -> None:
        self.assertIn(RequestStatus.DRAFT, AMENDABLE_STATUSES)
        self.assertIn(RequestStatus.SUBMITTED, AMENDABLE_STATUSES)
        self.assertIn(RequestStatus.QUEUED, AMENDABLE_STATUSES)

    def test_amendable_excludes_in_execution(self) -> None:
        self.assertNotIn(RequestStatus.IN_EXECUTION, AMENDABLE_STATUSES)

    def test_amendable_excludes_terminal_statuses(self) -> None:
        self.assertNotIn(RequestStatus.COMPLETED, AMENDABLE_STATUSES)
        self.assertNotIn(RequestStatus.CANCELED, AMENDABLE_STATUSES)

    def test_cancelable_excludes_terminal(self) -> None:
        self.assertNotIn(RequestStatus.COMPLETED, CANCELABLE_STATUSES)
        self.assertNotIn(RequestStatus.CANCELED, CANCELABLE_STATUSES)
        self.assertNotIn(RequestStatus.PROMOTED, CANCELABLE_STATUSES)


class SlaRiskTest(unittest.TestCase):
    def test_failed_request_is_critical(self) -> None:
        level, reason = compute_sla_risk("failed", "medium", None, datetime.now(timezone.utc))
        self.assertEqual(level, "critical")
        self.assertEqual(reason, "Execution failure")

    def test_urgent_under_threshold(self) -> None:
        level, reason = compute_sla_risk("queued", "urgent", None, datetime.now(timezone.utc))
        self.assertEqual(level, "high")
        self.assertIn("active SLA watch", reason)

    def test_urgent_over_threshold(self) -> None:
        old = datetime.now(timezone.utc) - timedelta(hours=3)
        level, reason = compute_sla_risk("queued", "urgent", None, old)
        self.assertEqual(level, "critical")
        self.assertIn("rapid-response", reason)

    def test_review_delay(self) -> None:
        old = datetime.now(timezone.utc) - timedelta(hours=5)
        level, reason = compute_sla_risk("awaiting_review", "medium", None, old)
        self.assertEqual(level, "high")
        self.assertEqual(reason, "Review delay")

    def test_promotion_delay(self) -> None:
        old = datetime.now(timezone.utc) - timedelta(hours=7)
        level, reason = compute_sla_risk("promotion_pending", "medium", None, old)
        self.assertEqual(level, "high")
        self.assertEqual(reason, "Promotion delay")

    def test_execution_delay(self) -> None:
        old = datetime.now(timezone.utc) - timedelta(hours=9)
        level, reason = compute_sla_risk("queued", "medium", None, old)
        self.assertEqual(level, "medium")
        self.assertEqual(reason, "Execution delay")

    def test_within_sla(self) -> None:
        level, reason = compute_sla_risk("queued", "medium", None, datetime.now(timezone.utc))
        self.assertIsNone(level)
        self.assertIsNone(reason)

    def test_unknown_policy_falls_back(self) -> None:
        level, reason = compute_sla_risk("failed", "medium", "nonexistent_policy", datetime.now(timezone.utc))
        self.assertEqual(level, "critical")

    def test_naive_updated_at_is_treated_as_utc(self) -> None:
        old = datetime.utcnow() - timedelta(hours=9)
        level, reason = compute_sla_risk("queued", "medium", None, old)
        self.assertEqual(level, "medium")
        self.assertEqual(reason, "Execution delay")

    def test_sla_policy_rules_structure(self) -> None:
        self.assertIn("sla_standard_v1", SLA_POLICY_RULES)
        policy = SLA_POLICY_RULES["sla_standard_v1"]
        for category in ("review_hours", "promotion_hours", "execution_hours"):
            self.assertIn(category, policy)
            for priority in ("medium", "high", "urgent"):
                self.assertIn(priority, policy[category])
                self.assertIsInstance(policy[category][priority], int)


if __name__ == "__main__":
    unittest.main()
