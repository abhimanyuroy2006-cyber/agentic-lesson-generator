"""
Automated tests verifying the Evaluator catches deliberate errors
and the Regenerator autonomously self-corrects them.
"""
import unittest
from src.graph import content_workflow
from src.models import RubricCheckpointId
from src.config import config
from src.memory import memory


class TestDeliberateErrors(unittest.TestCase):

    def setUp(self):
        config.provider = "mock"

    def test_evaluator_catches_jargon_bomb_and_remediates(self):
        """Test that a jargon-heavy draft fails rubric and is repaired on retry."""
        initial_state = {
            "topic": "Introduction to RAG",
            "iteration": 0,
            "max_retries": 2,
            "current_lesson": None,
            "latest_evaluation": None,
            "history": [],
            "rejection_log": [],
            "deliberate_error": "jargon_bomb",
            "status": "starting",
            "learned_guardrails": memory.get_learned_guardrails()
        }

        final_state = content_workflow.invoke(initial_state)

        # 1. Attempt 0 must have failed with jargon issues
        attempt_0_eval = final_state["history"][0]["evaluation"]
        self.assertFalse(attempt_0_eval["overall_passed"])
        failed_checkpoints = attempt_0_eval["failed_checkpoints"]
        has_jargon_fail = (
            RubricCheckpointId.NO_UNEXPLAINED_JARGON in failed_checkpoints or
            "no_unexplained_jargon" in failed_checkpoints
        )
        self.assertTrue(has_jargon_fail)

        # 2. Rejection log must record the failure
        self.assertGreaterEqual(len(final_state["rejection_log"]), 1)
        self.assertIn("jargon", str(final_state["rejection_log"][0]["failed_checkpoints"]).lower())

        # 3. Final state must have self-corrected and passed on retry 1
        self.assertEqual(final_state["status"], "passed")
        self.assertEqual(final_state["iteration"], 1)
        self.assertTrue(final_state["latest_evaluation"].overall_passed)

    def test_evaluator_catches_missing_analogy(self):
        """Test that an abstract draft without analogies fails TEACHES_BY_EXAMPLE and remediates."""
        initial_state = {
            "topic": "Introduction to RAG",
            "iteration": 0,
            "max_retries": 2,
            "current_lesson": None,
            "latest_evaluation": None,
            "history": [],
            "rejection_log": [],
            "deliberate_error": "missing_analogy",
            "status": "starting",
            "learned_guardrails": memory.get_learned_guardrails()
        }

        final_state = content_workflow.invoke(initial_state)

        # Attempt 0 fails TEACHES_BY_EXAMPLE
        attempt_0_eval = final_state["history"][0]["evaluation"]
        self.assertFalse(attempt_0_eval["overall_passed"])
        failed_cps = [str(c).lower() for c in attempt_0_eval["failed_checkpoints"]]
        self.assertTrue(any("teaches_by_example" in c for c in failed_cps))

        # Self-corrected on retry
        self.assertEqual(final_state["status"], "passed")
        self.assertEqual(final_state["iteration"], 1)

    def test_evaluator_catches_hallucination_and_memory_updates(self):
        """Test that inaccurate RAG claims fail ACCURACY_AND_GROUNDEDNESS."""
        initial_count = memory.state["checkpoint_failure_counts"].get(RubricCheckpointId.ACCURACY_AND_GROUNDEDNESS.value, 0)

        initial_state = {
            "topic": "Introduction to RAG",
            "iteration": 0,
            "max_retries": 2,
            "current_lesson": None,
            "latest_evaluation": None,
            "history": [],
            "rejection_log": [],
            "deliberate_error": "hallucination",
            "status": "starting",
            "learned_guardrails": memory.get_learned_guardrails()
        }

        final_state = content_workflow.invoke(initial_state)

        # Attempt 0 fails ACCURACY_AND_GROUNDEDNESS
        attempt_0_eval = final_state["history"][0]["evaluation"]
        self.assertFalse(attempt_0_eval["overall_passed"])
        failed_cps = [str(c).lower() for c in attempt_0_eval["failed_checkpoints"]]
        self.assertTrue(any("accurate_and_grounded" in c or "accuracy" in c for c in failed_cps))

        # Memory count must have increased
        updated_count = memory.state["checkpoint_failure_counts"].get(RubricCheckpointId.ACCURACY_AND_GROUNDEDNESS.value, 0)
        self.assertGreater(updated_count, initial_count)


if __name__ == "__main__":
    unittest.main()
