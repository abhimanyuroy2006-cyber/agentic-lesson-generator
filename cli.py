"""
Command Line Interface for the Self-Evaluating Lesson Content Generator.
Powered by Rich for visual terminal reporting.
"""
import argparse
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.tree import Tree

from src.graph import content_workflow
from src.config import config
from src.memory import memory
from src.models import RubricCheckpointId

console = Console()


def render_evaluation_table(eval_report, iteration: int):
    """Render a colored table of the 6 hard pass/fail checkpoints."""
    table = Table(
        title=f"Evaluator Audit - Attempt #{iteration} (Hard Pass/Fail Gate)",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("Checkpoint", style="cyan", width=30)
    table.add_column("Result", justify="center", width=10)
    table.add_column("Reason & Evidence", style="dim", width=60)

    for cp in eval_report.checkpoints:
        status_badge = "[bold green]PASS[/bold green]" if cp.passed else "[bold red]FAIL[/bold red]"
        reason_text = cp.reason
        if cp.violating_quote:
            reason_text += f"\n[bold red]Violating Quote:[/bold red] \"{cp.violating_quote}\""
        if cp.fix_recommendation:
            reason_text += f"\n[bold yellow]Fix Required:[/bold yellow] {cp.fix_recommendation}"
        table.add_row(cp.name, status_badge, reason_text)

    console.print(table)


def run_pipeline(topic: str, deliberate_error: str = None, max_retries: int = 2):
    """Execute the end-to-end LangGraph agentic loop."""
    console.print(Panel.fit(
        f"[bold cyan]Autonomous Lesson Generator: Self-Evaluating Content System[/bold cyan]\n"
        f"Topic: [yellow]{topic}[/yellow]\n"
        f"Learner Persona: [green]{config.persona.name}[/green]\n"
        f"Deliberate Error Mode: [bold red]{deliberate_error if deliberate_error else 'None (Clean)'}[/bold red]\n"
        f"LLM Provider: [bold magenta]{config.provider}[/bold magenta] (Active API: {config.is_api_configured()})",
        border_style="cyan"
    ))

    # Show active learned guardrails
    active_guardrails = memory.get_learned_guardrails()
    tree = Tree("[bold yellow]Active Evolved Guardrails from Memory[/bold yellow]")
    for g in active_guardrails:
        tree.add(f"[dim]{g}[/dim]")
    console.print(tree)
    console.print()

    # Initial State
    initial_state = {
        "topic": topic,
        "iteration": 0,
        "max_retries": max_retries,
        "current_lesson": None,
        "latest_evaluation": None,
        "history": [],
        "rejection_log": [],
        "deliberate_error": deliberate_error,
        "status": "starting",
        "learned_guardrails": active_guardrails
    }

    console.print("[bold blue]Starting LangGraph Execution Graph...[/bold blue]\n")
    
    # Run graph
    final_state = content_workflow.invoke(initial_state)

    # Display progression history
    for record_data in final_state["history"]:
        iter_idx = record_data["iteration_index"]
        eval_dict = record_data["evaluation"]
        
        from src.models import EvaluationReport
        eval_obj = EvaluationReport.model_validate(eval_dict)
        render_evaluation_table(eval_obj, iter_idx)
        console.print()

    # Status summary
    if final_state["status"] == "passed":
        console.print(Panel(
            f"[bold green]CONTENT CLEARED FOR PUBLICATION![/bold green]\n"
            f"The lesson cleared all 6 hard checkpoints on iteration #{final_state['iteration']}.",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold red]MAX RETRIES EXCEEDED ({max_retries})[/bold red]\n"
            f"Content could not clear all checkpoints automatically. Flagged for human review.",
            border_style="red"
        ))

    # Render Rejection Log if retries occurred
    if final_state["rejection_log"]:
        rej_table = Table(title="Rejection & Self-Correction Log", header_style="bold red")
        rej_table.add_column("Attempt", justify="center", width=8)
        rej_table.add_column("Failed Gates", width=25)
        rej_table.add_column("Why it Failed", width=40)
        rej_table.add_column("Remediation Action Applied", width=40)

        for entry in final_state["rejection_log"]:
            rej_table.add_row(
                str(entry["attempt_number"]),
                ", ".join(entry["failed_checkpoints"]),
                entry["why_it_failed"],
                entry["corrective_actions"]
            )
        console.print(rej_table)
        console.print()

    # Save output artifacts
    lesson = final_state["current_lesson"]
    if lesson:
        output_path = Path("FINAL_LESSON_DOCUMENT.md")
        content_md = (
            f"# {lesson.title}\n\n"
            f"> **Target Audience:** {config.persona.name} ({config.persona.education_level})\n"
            f"> **Status:** {final_state['status'].upper()} (Completed in {final_state['iteration'] + 1} attempt(s))\n\n"
            f"---\n\n"
            f"{lesson.content_markdown}\n"
        )
        output_path.write_text(content_md, encoding="utf-8")
        console.print(f"[bold green]Saved final lesson to:[/bold green] [underline]{output_path.resolve()}[/underline]")

    return final_state


def main():
    parser = argparse.ArgumentParser(description="Self-Evaluating Lesson Content Generator CLI")
    parser.add_argument("--topic", type=str, default="Introduction to RAG", help="Topic to generate")
    parser.add_argument(
        "--deliberate-error",
        type=str,
        choices=["jargon_bomb", "missing_analogy", "hallucination"],
        default=None,
        help="Trigger intentional failure mode for demonstration"
    )
    parser.add_argument("--max-retries", type=int, default=2, help="Maximum regeneration attempts")
    parser.add_argument("--provider", type=str, choices=["gemini", "openai", "mock"], default=None)

    args = parser.parse_args()

    if args.provider:
        config.provider = args.provider

    run_pipeline(
        topic=args.topic,
        deliberate_error=args.deliberate_error,
        max_retries=args.max_retries
    )


if __name__ == "__main__":
    main()
