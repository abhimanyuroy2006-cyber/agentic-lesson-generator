"""
Regenerator Agent: Executes targeted remediation based on evaluator critique.
Fixes failing sections while preserving validated content.
"""
from typing import List, Optional
from ..models import (
    LessonContent, EvaluationReport, RejectionLogEntry
)
from ..memory import memory
from ..llm import get_llm_client, MockLLMService
from ..config import config


def build_regeneration_prompt(
    topic: str,
    previous_content: str,
    critique: EvaluationReport,
    guardrails: List[str]
) -> str:
    """Create targeted remediation prompt containing exact failure reasons and quotes."""
    failures_text = []
    for cp in critique.checkpoints:
        if not cp.passed:
            item = f"- **{cp.name}**: {cp.reason}"
            if cp.violating_quote:
                item += f"\n  *Offending text*: \"{cp.violating_quote}\""
            if cp.fix_recommendation:
                item += f"\n  *Required Action*: {cp.fix_recommendation}"
            failures_text.append(item)

    failures_block = "\n".join(failures_text)
    guardrails_text = "\n".join([f"- {g}" for g in guardrails])

    prompt = f"""You are a specialized GenAI Content Engineer.
Your previous lesson draft on "{topic}" was REJECTED by our automated quality auditor.

=== AUDIT FAILURES TO FIX ===
{failures_block}

=== ACTIVE SYSTEM GUARDRAILS ===
{guardrails_text}

=== PREVIOUS DRAFT (NEEDS FIXING) ===
\"\"\"{previous_content}\"\"\"

=== TASK ===
Rewrite the lesson so that EVERY failed checkpoint passes.
1. Remove or replace all violating snippets highlighted above.
2. Keep sentences short (< 18 words) for a 12th-grade Indian student.
3. Integrate a relatable everyday analogy that clearly explains the topic.
4. Explain every technical or scientific term immediately in plain English.
5. Ensure accurate real-world facts strictly about "{topic}". Do not force fake tech or AI claims into general everyday topics. If the topic is RAG, clarify it does NOT retrain model weights.

Output the complete, revised markdown lesson.
"""
    return prompt


def regenerate_lesson(
    topic: str,
    previous_lesson: LessonContent,
    critique: EvaluationReport,
    attempt: int
) -> LessonContent:
    """Regenerate lesson draft using targeted feedback."""
    guardrails = memory.get_learned_guardrails()
    client = get_llm_client()

    # Log rejection in persistent rejection log
    violating_snippets = [cp.violating_quote for cp in critique.checkpoints if not cp.passed and cp.violating_quote]
    rejection_entry = RejectionLogEntry(
        attempt_number=attempt,
        topic=topic,
        failed_checkpoints=[cp.name for cp in critique.checkpoints if not cp.passed],
        why_it_failed=critique.summary_critique,
        violating_snippets=violating_snippets,
        corrective_actions="; ".join(critique.remediation_instructions)
    )
    memory.append_rejection_log(rejection_entry)

    if isinstance(client, MockLLMService):
        return client.regenerate_lesson(topic, previous_lesson, critique, guardrails)

    # Live LLM execution
    prompt = build_regeneration_prompt(topic, previous_lesson.content_markdown, critique, guardrails)
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content="You are an expert AI curriculum writer specializing in beginner-friendly remediation."),
            HumanMessage(content=prompt)
        ]
        response = client.invoke(messages)
        text = response.content if hasattr(response, "content") else str(response)

        return LessonContent(
            title=f"Introduction to {topic}",
            topic=topic,
            content_markdown=text,
            word_count=len(text.split()),
            analogies_used=["Open-Book vs Closed-Book Exam"],
            jargon_explained=["Retrieval", "Augment", "Generation", "Vector Database", "Hallucination"]
        )
    except Exception as e:
        print(f"[Regenerator] Live regeneration failed ({e}). Falling back to Mock service.")
        return MockLLMService.regenerate_lesson(topic, previous_lesson, critique, guardrails)
