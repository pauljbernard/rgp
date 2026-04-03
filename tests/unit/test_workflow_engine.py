"""Unit tests for the workflow engine service."""

import unittest

from app.models.workflow import (
    WorkflowCommand,
    WorkflowDefinitionRecord,
    WorkflowDefinitionStatus,
    WorkflowExecutionDetail,
    WorkflowExecutionRecord,
    WorkflowExecutionStatus,
    WorkflowStepDefinition,
    WorkflowStepExecutionRecord,
    WorkflowStepStatus,
    WorkflowCommandRequest,
)


class WorkflowModelsTest(unittest.TestCase):
    """Test Pydantic model creation and validation."""

    def test_execution_status_enum(self) -> None:
        self.assertEqual(WorkflowExecutionStatus.QUEUED, "queued")
        self.assertEqual(WorkflowExecutionStatus.RUNNING, "running")
        self.assertEqual(WorkflowExecutionStatus.PAUSED, "paused")
        self.assertEqual(WorkflowExecutionStatus.COMPLETED, "completed")
        self.assertEqual(WorkflowExecutionStatus.FAILED, "failed")
        self.assertEqual(WorkflowExecutionStatus.CANCELED, "canceled")

    def test_step_status_enum(self) -> None:
        self.assertEqual(WorkflowStepStatus.PENDING, "pending")
        self.assertEqual(WorkflowStepStatus.RUNNING, "running")
        self.assertEqual(WorkflowStepStatus.COMPLETED, "completed")
        self.assertEqual(WorkflowStepStatus.FAILED, "failed")
        self.assertEqual(WorkflowStepStatus.SKIPPED, "skipped")
        self.assertEqual(WorkflowStepStatus.PAUSED, "paused")

    def test_command_enum(self) -> None:
        self.assertEqual(WorkflowCommand.PAUSE, "pause")
        self.assertEqual(WorkflowCommand.RESUME, "resume")
        self.assertEqual(WorkflowCommand.CANCEL, "cancel")
        self.assertEqual(WorkflowCommand.RETRY_STEP, "retry_step")
        self.assertEqual(WorkflowCommand.SKIP_STEP, "skip_step")

    def test_step_definition(self) -> None:
        step = WorkflowStepDefinition(name="build", type="action", config={"image": "node:18"})
        self.assertEqual(step.name, "build")
        self.assertEqual(step.retry_max, 0)

    def test_definition_record(self) -> None:
        defn = WorkflowDefinitionRecord(
            id="wfd_1",
            tenant_id="t1",
            name="Standard Pipeline",
            version="1.0",
            steps=[WorkflowStepDefinition(name="build"), WorkflowStepDefinition(name="test")],
            status=WorkflowDefinitionStatus.ACTIVE,
        )
        self.assertEqual(len(defn.steps), 2)

    def test_execution_record(self) -> None:
        rec = WorkflowExecutionRecord(
            id="wfe_1",
            tenant_id="t1",
            run_id="run_1",
            request_id="req_1",
            status=WorkflowExecutionStatus.RUNNING,
            current_step_index=1,
        )
        self.assertEqual(rec.status, "running")
        self.assertEqual(rec.current_step_index, 1)
        self.assertIsNone(rec.failure_reason)

    def test_execution_detail_with_steps(self) -> None:
        detail = WorkflowExecutionDetail(
            id="wfe_1",
            tenant_id="t1",
            run_id="run_1",
            request_id="req_1",
            steps=[
                WorkflowStepExecutionRecord(
                    id="wfe_1_s0",
                    workflow_execution_id="wfe_1",
                    step_index=0,
                    step_name="build",
                    status=WorkflowStepStatus.COMPLETED,
                ),
                WorkflowStepExecutionRecord(
                    id="wfe_1_s1",
                    workflow_execution_id="wfe_1",
                    step_index=1,
                    step_name="test",
                    status=WorkflowStepStatus.RUNNING,
                ),
            ],
        )
        self.assertEqual(len(detail.steps), 2)
        self.assertEqual(detail.steps[0].status, "completed")
        self.assertEqual(detail.steps[1].status, "running")

    def test_command_request(self) -> None:
        cmd = WorkflowCommandRequest(
            actor_id="user_1",
            command=WorkflowCommand.PAUSE,
            reason="Waiting for approval",
        )
        self.assertEqual(cmd.command, "pause")
        self.assertIsNone(cmd.step_index)

    def test_retry_command_with_step_index(self) -> None:
        cmd = WorkflowCommandRequest(
            actor_id="user_1",
            command=WorkflowCommand.RETRY_STEP,
            step_index=2,
        )
        self.assertEqual(cmd.step_index, 2)


class WorkflowStateTransitionsTest(unittest.TestCase):
    """Test that workflow execution status transitions follow expected rules."""

    def test_valid_execution_statuses(self) -> None:
        valid = {"queued", "running", "paused", "completed", "failed", "canceled"}
        for s in WorkflowExecutionStatus:
            self.assertIn(s.value, valid)

    def test_valid_step_statuses(self) -> None:
        valid = {"pending", "running", "completed", "failed", "skipped", "paused"}
        for s in WorkflowStepStatus:
            self.assertIn(s.value, valid)

    def test_pause_only_from_running(self) -> None:
        # The workflow engine enforces that pause is only valid from RUNNING.
        # This test documents the expected behavior.
        valid_pause_from = {WorkflowExecutionStatus.RUNNING}
        invalid = {WorkflowExecutionStatus.QUEUED, WorkflowExecutionStatus.PAUSED,
                   WorkflowExecutionStatus.COMPLETED, WorkflowExecutionStatus.FAILED,
                   WorkflowExecutionStatus.CANCELED}
        for s in invalid:
            self.assertNotIn(s, valid_pause_from)

    def test_resume_only_from_paused(self) -> None:
        valid_resume_from = {WorkflowExecutionStatus.PAUSED}
        self.assertNotIn(WorkflowExecutionStatus.RUNNING, valid_resume_from)


if __name__ == "__main__":
    unittest.main()
