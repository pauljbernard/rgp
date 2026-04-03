"""Unit tests for the check type registry."""

import unittest

from app.domain.check_registry import (
    CheckContext,
    CheckRegistry,
    CheckResult,
    check_registry,
)


class CheckRegistryTest(unittest.TestCase):
    def test_builtins_registered(self) -> None:
        names = check_registry.list_names()
        self.assertIn("Intake Completeness", names)
        self.assertIn("Review Package Readiness", names)
        self.assertIn("Approval Freshness", names)
        self.assertIn("Policy Bundle", names)
        self.assertIn("Promotion Approval Freshness", names)

    def test_has(self) -> None:
        self.assertTrue(check_registry.has("Intake Completeness"))
        self.assertFalse(check_registry.has("Nonexistent Check"))

    def test_evaluate_unknown_raises(self) -> None:
        with self.assertRaises(KeyError):
            check_registry.evaluate("Nonexistent Check", CheckContext())

    def test_register_custom(self) -> None:
        registry = CheckRegistry()

        def custom_handler(ctx: CheckContext) -> CheckResult:
            return CheckResult(state="passed", detail="Custom OK", evidence="custom")

        registry.register("My Custom Check", custom_handler)
        self.assertTrue(registry.has("My Custom Check"))
        result = registry.evaluate("My Custom Check", CheckContext())
        self.assertEqual(result.state, "passed")
        self.assertEqual(result.detail, "Custom OK")

    def test_unregister(self) -> None:
        registry = CheckRegistry()
        registry.unregister("Intake Completeness")
        self.assertFalse(registry.has("Intake Completeness"))

    def test_evaluate_all(self) -> None:
        ctx = CheckContext(title="Test", summary="Summary", template_id="tpl_1")
        results = check_registry.evaluate_all(["Intake Completeness", "Nonexistent"], ctx)
        self.assertIn("Intake Completeness", results)
        self.assertNotIn("Nonexistent", results)


class IntakeCompletenessCheckTest(unittest.TestCase):
    def test_passes_when_all_fields_present(self) -> None:
        ctx = CheckContext(title="Test Request", summary="A summary", template_id="tpl_001")
        result = check_registry.evaluate("Intake Completeness", ctx)
        self.assertEqual(result.state, "passed")

    def test_fails_when_title_empty(self) -> None:
        ctx = CheckContext(title="", summary="A summary", template_id="tpl_001")
        result = check_registry.evaluate("Intake Completeness", ctx)
        self.assertEqual(result.state, "failed")

    def test_fails_when_whitespace_only(self) -> None:
        ctx = CheckContext(title="   ", summary="A summary", template_id="tpl_001")
        result = check_registry.evaluate("Intake Completeness", ctx)
        self.assertEqual(result.state, "failed")


class ReviewPackageReadinessCheckTest(unittest.TestCase):
    def test_passes_when_artifact_and_review_present(self) -> None:
        ctx = CheckContext(has_artifact=True, has_review=True)
        result = check_registry.evaluate("Review Package Readiness", ctx)
        self.assertEqual(result.state, "passed")

    def test_pending_when_artifact_missing(self) -> None:
        ctx = CheckContext(has_artifact=False, has_review=True)
        result = check_registry.evaluate("Review Package Readiness", ctx)
        self.assertEqual(result.state, "pending")


class ApprovalFreshnessCheckTest(unittest.TestCase):
    def test_passes_when_fresh_and_approved(self) -> None:
        ctx = CheckContext(has_artifact=True, artifact_stale_review=False, has_review=True, review_blocking_status="Approved")
        result = check_registry.evaluate("Approval Freshness", ctx)
        self.assertEqual(result.state, "passed")

    def test_pending_when_stale(self) -> None:
        ctx = CheckContext(has_artifact=True, artifact_stale_review=True, has_review=True, review_blocking_status="Approved")
        result = check_registry.evaluate("Approval Freshness", ctx)
        self.assertEqual(result.state, "pending")


class PolicyBundleCheckTest(unittest.TestCase):
    def test_passes_by_default(self) -> None:
        ctx = CheckContext(policy_context={})
        result = check_registry.evaluate("Policy Bundle", ctx)
        self.assertEqual(result.state, "passed")

    def test_fails_when_explicitly_false(self) -> None:
        ctx = CheckContext(policy_context={"policy_bundle_passed": False})
        result = check_registry.evaluate("Policy Bundle", ctx)
        self.assertEqual(result.state, "failed")


class CheckContextTest(unittest.TestCase):
    def test_defaults(self) -> None:
        ctx = CheckContext()
        self.assertEqual(ctx.request_id, "")
        self.assertEqual(ctx.title, "")
        self.assertFalse(ctx.has_artifact)
        self.assertEqual(ctx.policy_context, {})
        self.assertEqual(ctx.extra, {})

    def test_custom_values(self) -> None:
        ctx = CheckContext(request_id="req_1", title="My Request", extra={"custom": True})
        self.assertEqual(ctx.request_id, "req_1")
        self.assertTrue(ctx.extra["custom"])


if __name__ == "__main__":
    unittest.main()
