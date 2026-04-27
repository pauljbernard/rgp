import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from app.services.queue_routing_service import QueueRoutingService


class DummyQuery:
    def __init__(self, rows):
        self._rows = rows

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self._rows


class DummySession:
    def __init__(self, node_rows):
        self._node_rows = node_rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, model):
        return DummyQuery(self._node_rows)


class QueueRoutingServiceRoutingTest(unittest.TestCase):
    def test_recommend_assignment_excludes_restricted_draining_and_not_ready_nodes(self) -> None:
        service = QueueRoutingService()
        request = SimpleNamespace(
            id="req_001",
            request_type="assessment",
            priority="high",
            tags=["review"],
        )
        nodes = [
            SimpleNamespace(
                id="node_restricted",
                tenant_id="tenant_demo",
                name="Restricted Node",
                employment_model="contractor",
                trust_tier="restricted",
                billing_profile="contractor_fixed_rate",
                readiness_state="ready",
                drain_state="active",
                current_load=0,
                routing_tags=["review"],
                capabilities=["assessment"],
            ),
            SimpleNamespace(
                id="node_draining",
                tenant_id="tenant_demo",
                name="Draining Node",
                employment_model="employee",
                trust_tier="trusted",
                billing_profile="organization_funded",
                readiness_state="ready",
                drain_state="draining",
                current_load=0,
                routing_tags=["review"],
                capabilities=["assessment"],
            ),
            SimpleNamespace(
                id="node_attention",
                tenant_id="tenant_demo",
                name="Attention Node",
                employment_model="employee",
                trust_tier="trusted",
                billing_profile="organization_funded",
                readiness_state="attention_required",
                drain_state="active",
                current_load=0,
                routing_tags=["review"],
                capabilities=["assessment"],
            ),
            SimpleNamespace(
                id="node_good",
                tenant_id="tenant_demo",
                name="Trusted Employee Node",
                employment_model="employee",
                trust_tier="trusted",
                billing_profile="organization_funded",
                readiness_state="ready",
                drain_state="active",
                current_load=1,
                routing_tags=["review"],
                capabilities=["assessment"],
            ),
        ]
        with patch("app.services.queue_routing_service.get_request_state", return_value=request),              patch.object(service, "route_by_skill", return_value={"id": "ag_001", "name": "Assessment Reviewers", "skill_tags": ["review"], "current_load": 2, "max_capacity": 6}),              patch.object(service, "route_by_capacity", return_value=None),              patch("app.services.queue_routing_service.SessionLocal", return_value=DummySession(nodes)):
            recommendation = service.recommend_assignment("req_001", "tenant_demo")

        self.assertEqual(recommendation["recommended_node_id"], "node_good")
        self.assertEqual(recommendation["recommended_node_employment_model"], "employee")
        self.assertTrue(any("priority posture requires trusted employee nodes for high work" in item for item in recommendation["fleet_basis"]))
        self.assertTrue(any("excluded nodes:" in item for item in recommendation["fleet_basis"]))

    def test_recommend_assignment_falls_back_to_contractor_when_no_ready_employee_exists(self) -> None:
        service = QueueRoutingService()
        request = SimpleNamespace(
            id="req_002",
            request_type="assessment",
            priority="high",
            tags=["review"],
        )
        nodes = [
            SimpleNamespace(
                id="node_employee_not_ready",
                tenant_id="tenant_demo",
                name="Employee Not Ready",
                employment_model="employee",
                trust_tier="trusted",
                billing_profile="organization_funded",
                readiness_state="attention_required",
                drain_state="active",
                current_load=0,
                routing_tags=["review"],
                capabilities=["assessment"],
            ),
            SimpleNamespace(
                id="node_contractor",
                tenant_id="tenant_demo",
                name="Elevated Contractor Node",
                employment_model="contractor",
                trust_tier="elevated",
                billing_profile="contractor_fixed_rate",
                readiness_state="ready",
                drain_state="active",
                current_load=0,
                routing_tags=["review"],
                capabilities=["assessment"],
            ),
        ]
        with patch("app.services.queue_routing_service.get_request_state", return_value=request),              patch.object(service, "route_by_skill", return_value={"id": "ag_001", "name": "Assessment Reviewers", "skill_tags": ["review"], "current_load": 2, "max_capacity": 6}),              patch.object(service, "route_by_capacity", return_value=None),              patch("app.services.queue_routing_service.SessionLocal", return_value=DummySession(nodes)):
            recommendation = service.recommend_assignment("req_002", "tenant_demo")

        self.assertEqual(recommendation["recommended_node_id"], "node_contractor")
        self.assertEqual(recommendation["recommended_node_employment_model"], "contractor")
        self.assertTrue(any("trust posture requires elevated or trusted nodes for high work" in item for item in recommendation["fleet_basis"]))

    def test_recommend_assignment_uses_cost_aware_contractor_fallback_for_medium_priority_when_employee_load_is_saturated(self) -> None:
        service = QueueRoutingService()
        request = SimpleNamespace(
            id="req_003",
            request_type="assessment",
            priority="medium",
            tags=["review"],
        )
        nodes = [
            SimpleNamespace(
                id="node_employee_busy",
                tenant_id="tenant_demo",
                name="Busy Employee Node",
                employment_model="employee",
                trust_tier="trusted",
                billing_profile="organization_funded",
                readiness_state="ready",
                drain_state="active",
                current_load=4,
                routing_tags=["review"],
                capabilities=["assessment"],
            ),
            SimpleNamespace(
                id="node_contractor_fixed",
                tenant_id="tenant_demo",
                name="Fixed Rate Contractor Node",
                employment_model="contractor",
                trust_tier="elevated",
                billing_profile="contractor_fixed_rate",
                readiness_state="ready",
                drain_state="active",
                current_load=1,
                routing_tags=["review"],
                capabilities=["assessment"],
            ),
        ]
        with patch("app.services.queue_routing_service.get_request_state", return_value=request),              patch.object(service, "route_by_skill", return_value={"id": "ag_001", "name": "Assessment Reviewers", "skill_tags": ["review"], "current_load": 2, "max_capacity": 6}),              patch.object(service, "route_by_capacity", return_value=None),              patch("app.services.queue_routing_service.SessionLocal", return_value=DummySession(nodes)):
            recommendation = service.recommend_assignment("req_003", "tenant_demo")

        self.assertEqual(recommendation["recommended_node_id"], "node_contractor_fixed")
        self.assertTrue(any("cost-aware contractor fallback" in item for item in recommendation["fleet_basis"]))

    def test_recommend_assignment_keeps_high_priority_work_on_ready_employee_nodes_when_available(self) -> None:
        service = QueueRoutingService()
        request = SimpleNamespace(
            id="req_004",
            request_type="assessment",
            priority="urgent",
            tags=["review"],
        )
        nodes = [
            SimpleNamespace(
                id="node_employee_busy",
                tenant_id="tenant_demo",
                name="Busy Employee Node",
                employment_model="employee",
                trust_tier="trusted",
                billing_profile="organization_funded",
                readiness_state="ready",
                drain_state="active",
                current_load=5,
                routing_tags=["review"],
                capabilities=["assessment"],
            ),
            SimpleNamespace(
                id="node_contractor_fixed",
                tenant_id="tenant_demo",
                name="Fixed Rate Contractor Node",
                employment_model="contractor",
                trust_tier="elevated",
                billing_profile="contractor_fixed_rate",
                readiness_state="ready",
                drain_state="active",
                current_load=0,
                routing_tags=["review"],
                capabilities=["assessment"],
            ),
        ]
        with patch("app.services.queue_routing_service.get_request_state", return_value=request),              patch.object(service, "route_by_skill", return_value={"id": "ag_001", "name": "Assessment Reviewers", "skill_tags": ["review"], "current_load": 2, "max_capacity": 6}),              patch.object(service, "route_by_capacity", return_value=None),              patch("app.services.queue_routing_service.SessionLocal", return_value=DummySession(nodes)):
            recommendation = service.recommend_assignment("req_004", "tenant_demo")

        self.assertEqual(recommendation["recommended_node_id"], "node_employee_busy")
        self.assertTrue(any("priority posture requires trusted employee nodes for urgent work" in item for item in recommendation["fleet_basis"]))
        self.assertTrue(any("trust gate: elevated-or-better required for urgent work" in item for item in recommendation["fleet_basis"]))

    def test_recommend_assignment_rejects_standard_trust_for_urgent_work_when_elevated_node_exists(self) -> None:
        service = QueueRoutingService()
        request = SimpleNamespace(
            id="req_005",
            request_type="assessment",
            priority="urgent",
            tags=["review"],
        )
        nodes = [
            SimpleNamespace(
                id="node_standard_contractor",
                tenant_id="tenant_demo",
                name="Standard Contractor Node",
                employment_model="contractor",
                trust_tier="standard",
                billing_profile="contractor_fixed_rate",
                readiness_state="ready",
                drain_state="active",
                current_load=0,
                routing_tags=["review"],
                capabilities=["assessment"],
            ),
            SimpleNamespace(
                id="node_elevated_contractor",
                tenant_id="tenant_demo",
                name="Elevated Contractor Node",
                employment_model="contractor",
                trust_tier="elevated",
                billing_profile="contractor_fixed_rate",
                readiness_state="ready",
                drain_state="active",
                current_load=1,
                routing_tags=["review"],
                capabilities=["assessment"],
            ),
        ]
        with patch("app.services.queue_routing_service.get_request_state", return_value=request),              patch.object(service, "route_by_skill", return_value={"id": "ag_001", "name": "Assessment Reviewers", "skill_tags": ["review"], "current_load": 2, "max_capacity": 6}),              patch.object(service, "route_by_capacity", return_value=None),              patch("app.services.queue_routing_service.SessionLocal", return_value=DummySession(nodes)):
            recommendation = service.recommend_assignment("req_005", "tenant_demo")

        self.assertEqual(recommendation["recommended_node_id"], "node_elevated_contractor")
        self.assertTrue(any("trust posture requires elevated or trusted nodes for urgent work" in item for item in recommendation["fleet_basis"]))
        self.assertTrue(any("employee capacity posture: no ready employee nodes" in item for item in recommendation["fleet_basis"]))


if __name__ == "__main__":
    unittest.main()
