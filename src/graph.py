"""
LangGraph StateGraph Orchestration: Implements the Generate -> Evaluate -> Regenerate loop.
Guarantees bounded retries, self-evolving memory integration, and structured auditability.
"""
from typing import Dict, Any, Literal
from datetime import datetime
from langgraph.graph import StateGraph, END
from .models import WorkflowState, IterationRecord, RejectionLogEntry
from .agents.generator import generate_lesson
from .agents.evaluator import evaluate_lesson
from .agents.regenerator import regenerate_lesson
from .memory import memory
from .config import config


def node_generate(state: WorkflowState) -> Dict[str, Any]:
    """Generator Node: Produces the initial lesson draft."""
    topic = state["topic"]
    deliberate_error = state.get("deliberate_error")
    
    lesson = generate_lesson(topic=topic, deliberate_error=deliberate_error)
    
    # Deliberate error is consumed on initial generation
    return {
        "current_lesson": lesson,
        "deliberate_error": None,
        "status": "evaluating"
    }


def node_evaluate(state: WorkflowState) -> Dict[str, Any]:
    """Evaluator Node: Runs the 6 hard pass/fail checkpoints."""
    lesson = state["current_lesson"]
    topic = state["topic"]
    iteration = state["iteration"]
    
    evaluation = evaluate_lesson(lesson)
    
    # Record iteration snapshot
    record = IterationRecord(
        iteration_index=iteration,
        lesson=lesson,
        evaluation=evaluation,
        remediation_applied="; ".join(evaluation.remediation_instructions) if not evaluation.overall_passed else None,
        timestamp=datetime.now().isoformat()
    )
    
    new_history = list(state.get("history", []))
    new_history.append(record.model_dump(mode="json"))
    
    # If failed, update memory statistics and trigger self-evolution
    if not evaluation.overall_passed:
        memory.record_iteration_failure(
            topic=topic,
            attempt=iteration,
            eval_report=evaluation,
            lesson=lesson
        )
    
    return {
        "latest_evaluation": evaluation,
        "history": new_history,
        "learned_guardrails": memory.get_learned_guardrails()
    }


def decide_next_step(state: WorkflowState) -> Literal["node_regenerate", "node_success", "node_max_retries"]:
    """Conditional Edge: Decides whether to ship, regenerate, or terminate."""
    evaluation = state["latest_evaluation"]
    iteration = state["iteration"]
    max_retries = state["max_retries"]
    
    if evaluation and evaluation.overall_passed:
        return "node_success"
    
    if iteration < max_retries:
        return "node_regenerate"
    
    return "node_max_retries"


def node_regenerate(state: WorkflowState) -> Dict[str, Any]:
    """Regenerator Node: Applies targeted fixes based on critique."""
    topic = state["topic"]
    iteration = state["iteration"] + 1
    previous_lesson = state["current_lesson"]
    evaluation = state["latest_evaluation"]
    
    # Rejection log tracking
    rejection_entry = RejectionLogEntry(
        attempt_number=iteration - 1,
        topic=topic,
        failed_checkpoints=[cp.name for cp in evaluation.checkpoints if not cp.passed],
        why_it_failed=evaluation.summary_critique,
        violating_snippets=[cp.violating_quote for cp in evaluation.checkpoints if not cp.passed and cp.violating_quote],
        corrective_actions="; ".join(evaluation.remediation_instructions)
    )
    new_rejection_log = list(state.get("rejection_log", []))
    new_rejection_log.append(rejection_entry.model_dump(mode="json"))
    
    # Regenerate content
    revised_lesson = regenerate_lesson(
        topic=topic,
        previous_lesson=previous_lesson,
        critique=evaluation,
        attempt=iteration
    )
    
    return {
        "iteration": iteration,
        "current_lesson": revised_lesson,
        "rejection_log": new_rejection_log,
        "status": "evaluating"
    }


def node_success(state: WorkflowState) -> Dict[str, Any]:
    """Terminal Success Node: Persists shipping lesson."""
    memory.record_run_completion(
        topic=state["topic"],
        passed=True,
        total_iterations=state["iteration"] + 1,
        history=state["history"]
    )
    return {"status": "passed"}


def node_max_retries(state: WorkflowState) -> Dict[str, Any]:
    """Terminal Node when maximum retries are reached."""
    memory.record_run_completion(
        topic=state["topic"],
        passed=False,
        total_iterations=state["iteration"] + 1,
        history=state["history"]
    )
    return {"status": "max_retries_exceeded"}


def build_workflow() -> StateGraph:
    """Construct the compiled LangGraph workflow graph."""
    graph = StateGraph(WorkflowState)
    
    # Add nodes
    graph.add_node("node_generate", node_generate)
    graph.add_node("node_evaluate", node_evaluate)
    graph.add_node("node_regenerate", node_regenerate)
    graph.add_node("node_success", node_success)
    graph.add_node("node_max_retries", node_max_retries)
    
    # Entry point
    graph.set_entry_point("node_generate")
    
    # Flow
    graph.add_edge("node_generate", "node_evaluate")
    
    # Conditional branching after evaluation
    graph.add_conditional_edges(
        "node_evaluate",
        decide_next_step,
        {
            "node_regenerate": "node_regenerate",
            "node_success": "node_success",
            "node_max_retries": "node_max_retries"
        }
    )
    
    # Loop back from regenerator to evaluator
    graph.add_edge("node_regenerate", "node_evaluate")
    
    # Terminal edges
    graph.add_edge("node_success", END)
    graph.add_edge("node_max_retries", END)
    
    return graph.compile()


# Compile graph instance
content_workflow = build_workflow()
