"""
Persistent Memory and Self-Evolving Feedback System.
Learns from repeated evaluation failures across runs to dynamically synthesize and sharpen generator guardrails.
"""
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from .models import RubricCheckpointId, EvaluationReport, LessonContent, RejectionLogEntry
from .config import config


class MemoryManager:
    """
    Manages cross-run persistence and dynamic prompt evolution.
    When checkpoints fail repeatedly, it derives and injects sharpened constraints.
    """

    def __init__(self, memory_file: Path = config.memory_path, log_file: Path = config.rejection_log_path):
        self.memory_file = memory_file
        self.log_file = log_file
        self.state: Dict[str, Any] = self._load_memory()

    def _load_memory(self) -> Dict[str, Any]:
        """Load state from disk or initialize fresh structure."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "checkpoint_failure_counts": {cp.value: 0 for cp in RubricCheckpointId},
            "recurring_mistakes": [],
            "learned_guardrails": [
                "Always use simple everyday words; avoid multi-syllable academic phrasing.",
                "Translate any AI technical term into plain English in parentheses or in the very next sentence.",
                "Frame the core problem using the 'Closed-Book vs. Open-Book Exam' analogy."
            ],
            "runs": []
        }

    def _save_memory(self):
        """Persist updated state to disk."""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def get_learned_guardrails(self) -> List[str]:
        """Retrieve active guardrails derived from historical learning."""
        return self.state.get("learned_guardrails", [])

    def record_iteration_failure(self, topic: str, attempt: int, eval_report: EvaluationReport, lesson: LessonContent):
        """Record a failure event and update frequency statistics."""
        for failed_id in eval_report.failed_checkpoints:
            cp_key = failed_id.value if isinstance(failed_id, RubricCheckpointId) else str(failed_id)
            self.state["checkpoint_failure_counts"][cp_key] = (
                self.state["checkpoint_failure_counts"].get(cp_key, 0) + 1
            )
            
            # Record concrete failure pattern
            mistake_entry = {
                "timestamp": datetime.now().isoformat(),
                "topic": topic,
                "attempt": attempt,
                "checkpoint": cp_key,
                "summary": eval_report.summary_critique,
                "remediations": eval_report.remediation_instructions
            }
            self.state["recurring_mistakes"].append(mistake_entry)

        # Trigger self-evolution of rules if failure thresholds are reached
        self._evolve_guardrails()
        self._save_memory()

    def _evolve_guardrails(self):
        """
        Self-evolving rule synthesizer: analyzes recurring failure modes
        and automatically sharpens prompt constraints.
        """
        counts = self.state["checkpoint_failure_counts"]
        evolved = list(self.state.get("learned_guardrails", []))

        # Checkpoint: NO_UNEXPLAINED_JARGON
        if counts.get(RubricCheckpointId.NO_UNEXPLAINED_JARGON.value, 0) >= 1:
            rule = (
                "STRICT SHARPENED GUARDRAIL (From Memory): Never introduce technical or scientific jargon "
                "without an immediate, simple 1-sentence plain-English translation before continuing."
            )
            if rule not in evolved:
                evolved.append(rule)

        # Checkpoint: TEACHES_BY_EXAMPLE
        if counts.get(RubricCheckpointId.TEACHES_BY_EXAMPLE.value, 0) >= 1:
            rule = (
                "STRICT SHARPENED GUARDRAIL (From Memory): Dedicate an entire early section to a relatable everyday analogy "
                "(such as school exams, kitchen cooking, sports, or nature) to anchor the concept before touching complex details."
            )
            if rule not in evolved:
                evolved.append(rule)

        # Checkpoint: BEGINNER_FRIENDLY_LANGUAGE
        if counts.get(RubricCheckpointId.BEGINNER_FRIENDLY_LANGUAGE.value, 0) >= 1:
            rule = (
                "STRICT SHARPENED GUARDRAIL (From Memory): Keep sentences strictly under 18 words. "
                "Write as if explaining to a 12th-grade friend who studied in Hindi/regional medium."
            )
            if rule not in evolved:
                evolved.append(rule)

        # Checkpoint: ACCURACY_AND_GROUNDEDNESS
        if counts.get(RubricCheckpointId.ACCURACY_AND_GROUNDEDNESS.value, 0) >= 1:
            rule = (
                "STRICT SHARPENED GUARDRAIL (From Memory): Ground all explanations in true real-world facts without hallucinations "
                "(for AI topics like RAG, explicitly state that it does NOT retrain or alter model weights; for everyday topics, stick purely to authentic real-world facts)."
            )
            if rule not in evolved:
                evolved.append(rule)

        self.state["learned_guardrails"] = evolved

    def record_run_completion(self, topic: str, passed: bool, total_iterations: int, history: List[Any]):
        """Persist overall run completion status."""
        self.state["total_runs"] += 1
        if passed:
            self.state["successful_runs"] += 1
        else:
            self.state["failed_runs"] += 1

        run_summary = {
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "passed": passed,
            "iterations_required": total_iterations,
        }
        self.state["runs"].append(run_summary)
        self._save_memory()

    def append_rejection_log(self, entry: RejectionLogEntry):
        """Append to external audit rejection log."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        logs = []
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except Exception:
                logs = []
        logs.append(entry.model_dump())
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)


# Global singleton
memory = MemoryManager()
