"""
Evaluator Agent: Rigorously tests the lesson against 6 hard pass/fail checkpoints.
Applies deterministic heuristics and structured LLM evaluation. No partial credit.
"""
from typing import Dict, Any, List
import json
from ..models import (
    LessonContent, EvaluationReport, CheckpointResult, RubricCheckpointId
)
from ..rubric import RUBRIC_DEFINITIONS, heuristic_language_check
from ..llm import get_llm_client, MockLLMService


def evaluate_lesson(lesson: LessonContent) -> EvaluationReport:
    """Evaluate the lesson draft against all 6 hard pass/fail checkpoints."""
    heuristics = heuristic_language_check(lesson.content_markdown)
    client = get_llm_client()

    if isinstance(client, MockLLMService):
        report = client.evaluate_lesson(lesson)
        # Augment with heuristic signals
        if not heuristics["is_sentence_length_ok"]:
            for cp in report.checkpoints:
                if cp.checkpoint_id == RubricCheckpointId.BEGINNER_FRIENDLY_LANGUAGE and cp.passed:
                    cp.passed = False
                    cp.reason += f" Heuristic check failed: average sentence length is {heuristics['avg_sentence_length']} words (limit is 18)."
                    report.failed_checkpoints.append(RubricCheckpointId.BEGINNER_FRIENDLY_LANGUAGE)
                    report.overall_passed = False
        return report

    # Live LLM structured evaluation
    prompt = f"""You are a strict QA Rubric Evaluator for educational content.
Judge the following lesson against 6 HARD PASS/FAIL checkpoints.
There is NO PARTIAL CREDIT. Each check must strictly PASS (true) or FAIL (false).

=== LESSON TO EVALUATE ===
Title: {lesson.title}
Content:
\"\"\"{lesson.content_markdown}\"\"\"

=== HEURISTIC SIGNALS ===
Word Count: {heuristics['word_count']}
Average Sentence Length: {heuristics['avg_sentence_length']} words
Flagged Suspicious Jargon: {heuristics['suspicious_unexplained_terms']}
Analogy Present: {heuristics['has_analogy_keyword']}

=== 6 HARD PASS/FAIL CHECKPOINTS ===
1. accurate_and_grounded: Must accurately explain the topic using true real-world facts without hallucinations or errors (if the topic is AI/tech like RAG, verify it does not claim model weights are retrained; if it is an everyday or general topic like bath, apple, or tiger, verify authentic real-world facts without forced fake tech claims).
2. beginner_friendly_language: Simple English for 12th-grade Indian student. Sentences strictly average under 18 words.
3. teaches_by_example: Must contain a relatable everyday analogy or real-life comparison (e.g. school exam, cricket, cooking, sports, daily habits) that anchors understanding.
4. no_unexplained_jargon: Every technical or scientific buzzword must have an immediate 1-line plain-English explanation.
5. covers_key_points: Must cover What it is, Why it matters, and How it works or functions.
6. coherent_teaching_flow: Logical pedagogical progression.

Respond with valid JSON matching this schema (IMPORTANT: do not put unescaped double quotes inside strings; use single quotes instead):
{{
  "overall_passed": true/false,
  "checkpoints": [
    {{
      "checkpoint_id": "accurate_and_grounded",
      "name": "Accurate & Grounded",
      "passed": true/false,
      "reason": "Detailed justification",
      "violating_quote": "exact phrase if failed or null",
      "fix_recommendation": "how to fix if failed or null"
    }},
    ... (all 6 checkpoints)
  ],
  "summary_critique": "Brief overall critique",
  "remediation_instructions": ["Fix 1", "Fix 2"]
}}
"""

    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content="You are a strict JSON-only educational rubric auditor. Respond strictly in valid JSON format."),
            HumanMessage(content=prompt)
        ]
        response = client.invoke(messages)
        content_str = response.content if hasattr(response, "content") else str(response)

        # Clean JSON block
        if "```json" in content_str:
            content_str = content_str.split("```json")[1].split("```")[0].strip()
        elif "```" in content_str:
            content_str = content_str.split("```")[1].split("```")[0].strip()

        # Robust JSON parse
        try:
            data = json.loads(content_str)
        except Exception:
            # Fallback attempt: extract outer JSON
            import re
            m = re.search(r"(\{[\s\S]*\})", content_str)
            if m:
                # Replace unescaped control chars if any
                cleaned = re.sub(r'[\x00-\x1f]', ' ', m.group(1))
                data = json.loads(cleaned)
            else:
                raise
        checkpoints = []
        failed_ids = []

        for cp_data in data.get("checkpoints", []):
            cid = RubricCheckpointId(cp_data["checkpoint_id"])
            passed = bool(cp_data["passed"])
            if not passed:
                failed_ids.append(cid)
            checkpoints.append(CheckpointResult(
                checkpoint_id=cid,
                name=cp_data.get("name", cid.value),
                passed=passed,
                reason=cp_data.get("reason", ""),
                violating_quote=cp_data.get("violating_quote"),
                fix_recommendation=cp_data.get("fix_recommendation")
            ))

        overall_passed = len(failed_ids) == 0
        return EvaluationReport(
            overall_passed=overall_passed,
            checkpoints=checkpoints,
            failed_checkpoints=failed_ids,
            summary_critique=data.get("summary_critique", ""),
            remediation_instructions=data.get("remediation_instructions", [])
        )
    except Exception as e:
        print(f"[Evaluator] Live evaluation parsing failed ({e}). Falling back to Mock evaluator.")
        return MockLLMService.evaluate_lesson(lesson)
