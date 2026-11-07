"""
Pydantic data models and schemas for the Self-Evaluating Lesson Content Generator.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class RubricCheckpointId(str, Enum):
    """The 6 hard pass/fail rubric checkpoints."""
    ACCURACY_AND_GROUNDEDNESS = "accurate_and_grounded"
    BEGINNER_FRIENDLY_LANGUAGE = "beginner_friendly_language"
    TEACHES_BY_EXAMPLE = "teaches_by_example"
    NO_UNEXPLAINED_JARGON = "no_unexplained_jargon"
    COVERS_KEY_POINTS = "covers_key_points"
    COHERENT_TEACHING_FLOW = "coherent_teaching_flow"


class CheckpointResult(BaseModel):
    """Evaluation result for an individual rubric checkpoint. No partial credit."""
    checkpoint_id: RubricCheckpointId
    name: str = Field(description="Human-readable title of the checkpoint")
    passed: bool = Field(description="Hard pass (True) or fail (False). No partial points.")
    reason: str = Field(description="Concrete evidence and explanation for why it passed or failed")
    violating_quote: Optional[str] = Field(default=None, description="Exact problematic sentence or phrase if failed")
    fix_recommendation: Optional[str] = Field(default=None, description="Actionable instruction to resolve the failure")


class EvaluationReport(BaseModel):
    """Comprehensive evaluation report covering all 6 checkpoints."""
    overall_passed: bool = Field(description="True ONLY if every single checkpoint passed.")
    checkpoints: List[CheckpointResult] = Field(description="Results of each hard pass/fail checkpoint")
    failed_checkpoints: List[RubricCheckpointId] = Field(default_factory=list, description="IDs of failed checkpoints")
    summary_critique: str = Field(description="Holistic evaluation summary")
    remediation_instructions: List[str] = Field(default_factory=list, description="Targeted bullet points for the regenerator")


class LessonContent(BaseModel):
    """Structured lesson output generated for the learner."""
    title: str = Field(description="Engaging, non-intimidating lesson title")
    topic: str = Field(description="Core topic being taught")
    content_markdown: str = Field(description="Full lesson markdown text")
    word_count: int = Field(default=0, description="Approximate word count")
    analogies_used: List[str] = Field(default_factory=list, description="Everyday analogies featured in the text")
    jargon_explained: List[str] = Field(default_factory=list, description="List of technical terms defined in plain English")


class IterationRecord(BaseModel):
    """Audit log of a single generation & evaluation cycle."""
    iteration_index: int
    lesson: LessonContent
    evaluation: EvaluationReport
    remediation_applied: Optional[str] = None
    timestamp: str


class RejectionLogEntry(BaseModel):
    """Detailed record of a failed attempt explaining what broke and what was fixed."""
    attempt_number: int
    topic: str
    failed_checkpoints: List[str]
    why_it_failed: str
    violating_snippets: List[str]
    corrective_actions: str


class WorkflowState(TypedDict):
    """LangGraph workflow state dictionary."""
    topic: str
    iteration: int
    max_retries: int
    current_lesson: Optional[LessonContent]
    latest_evaluation: Optional[EvaluationReport]
    history: List[Dict[str, Any]]
    rejection_log: List[Dict[str, Any]]
    deliberate_error: Optional[str]  # e.g., 'jargon_bomb', 'missing_analogy', 'hallucination'
    status: str
    learned_guardrails: List[str]
