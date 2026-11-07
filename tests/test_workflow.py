"""
Unit and integration tests for the self-evaluating lesson content workflow.
"""
import unittest
from src.graph import content_workflow
from src.models import RubricCheckpointId
from src.config import config
from src.memory import memory


class TestContentWorkflow(unittest.TestCase):

    def setUp(self):
        config.provider = "mock"

    def test_clean_pipeline_run(self):
        """Verify clean run succeeds and passes all 6 rubric checkpoints."""
        initial_state = {
            "topic": "Introduction to RAG",
            "iteration": 0,
            "max_retries": 2,
            "current_lesson": None,
            "latest_evaluation": None,
            "history": [],
            "rejection_log": [],
            "deliberate_error": None,
            "status": "starting",
            "learned_guardrails": memory.get_learned_guardrails()
        }

        final_state = content_workflow.invoke(initial_state)

        self.assertEqual(final_state["status"], "passed")
        self.assertTrue(final_state["latest_evaluation"].overall_passed)
        self.assertEqual(len(final_state["latest_evaluation"].failed_checkpoints), 0)
        self.assertEqual(len(final_state["latest_evaluation"].checkpoints), 6)
        self.assertIsNotNone(final_state["current_lesson"])
        self.assertIn("Open-Book", final_state["current_lesson"].content_markdown)

    def test_bounded_loop_termination(self):
        """Ensure the state loop strictly terminates when max retries are reached."""
        initial_state = {
            "topic": "Introduction to RAG",
            "iteration": 0,
            "max_retries": 1,
            "current_lesson": None,
            "latest_evaluation": None,
            "history": [],
            "rejection_log": [],
            "deliberate_error": None,
            "status": "starting",
            "learned_guardrails": memory.get_learned_guardrails()
        }

        final_state = content_workflow.invoke(initial_state)
        self.assertIn(final_state["status"], ["passed", "max_retries_exceeded"])
        self.assertLessEqual(final_state["iteration"], 2)


if __name__ == "__main__":
    unittest.main()
