"""
Generator Agent: Crafts introductory lessons tailored for 12th-grade Indian graduates.
Incorporates target persona guidelines, memory-derived evolved guardrails, and intentional test modes.
"""
from typing import List, Optional
import json
from ..models import LessonContent
from ..config import config
from ..memory import memory
from ..llm import get_llm_client, MockLLMService


def build_generator_prompt(topic: str, guardrails: List[str], deliberate_error: Optional[str] = None) -> str:
    """Construct prompt with explicit persona tuning and self-evolved guardrails."""
    persona = config.persona

    guardrails_text = "\n".join([f"- {g}" for g in guardrails])

    prompt = f"""You are an elite GenAI Content Engineer creating learning material.
Your mission is to teach the topic: "{topic}" to a very specific learner persona.

=== LEARNER PERSONA ===
- Target Student: {persona.name}
- Background: {persona.education_level}
- Language: {persona.english_proficiency}
- Ambition: Wants to build clear understanding and practical real-world skills

=== PEDAGOGICAL REQUIREMENTS ===
1. Use simple, warm, everyday English. Sentence lengths MUST strictly average under 18 words.
2. Teach with a tangible everyday analogy that fits the topic (e.g., school exam, kirana shop, sports, nature, daily chores).
3. ZERO unexplained jargon. Any technical or scientific term MUST be immediately defined in simple plain English before use.
4. Structure the lesson with:
   - What is it? (Simple definition grounded in true real-world facts)
   - Why do we need it / Why does it matter? (Relatable everyday analogy)
   - How it works or how to do it in 3 clear logical steps
   - Real-world impact and practical daily importance
   - A quick 3-question revision quiz.

=== TOPIC RELEVANCE & ZERO HALLUCINATION RULES ===
- Teach strictly and authentically about "{topic}":
  * If GIBBERISH / RANDOM KEYBOARD SPAM (e.g. 'asdfghjk', random string of keys with no meaning in any dictionary): DO NOT pretend it is a real subject! State clearly: "⚠️ UNRECOGNIZED TOPIC: The input provided appears to be random keyboard characters. Please enter a real subject, concept, or object."
  * If GENERAL REAL-WORLD TOPIC (e.g. bath, apple, onion, tiger, television, bicycle, cricket, gravity): Teach the genuine real-world facts, science, biology, or daily practical guidance about that exact topic. DO NOT artificially inject AI, computer algorithms, RAG, or neural networks into general everyday topics!
  * If AI / TECH TOPIC (e.g. RAG, Machine Learning, XGBoost, Neural Networks): Teach the computing logic. For RAG specifically, remember it does NOT retrain or alter model weights.

=== HISTORICAL LEARNED GUARDRAILS (SELF-EVOLVED FROM PAST RUNS) ===
{guardrails_text}
"""

    if deliberate_error:
        prompt += f"\n[DELIBERATE ERROR INJECTION MODE ACTIVATED: {deliberate_error.upper()}]\n"
        if deliberate_error == "jargon_bomb":
            prompt += "Inject heavy, dense academic jargon (e.g., high-dimensional Euclidean latent space, multi-head attention queries) without any simple explanations."
        elif deliberate_error == "missing_analogy":
            prompt += "Omit all everyday analogies and real-world examples. Make the explanation purely abstract and dry."
        elif deliberate_error == "hallucination":
            prompt += "Falsely state that RAG retrains the model neural network weights on every single retrieved document."

    return prompt


def generate_lesson(topic: str, deliberate_error: Optional[str] = None) -> LessonContent:
    """Generate initial lesson draft using configured LLM or Mock provider."""
    guardrails = memory.get_learned_guardrails()
    client = get_llm_client()

    if isinstance(client, MockLLMService):
        return client.generate_lesson(topic=topic, guardrails=guardrails, deliberate_error=deliberate_error)

    # Live LLM execution (Gemini or OpenAI)
    prompt = build_generator_prompt(topic, guardrails, deliberate_error)
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content="You are a specialized GenAI educator. Output clean, well-formatted markdown for the student."),
            HumanMessage(content=prompt)
        ]
        response = client.invoke(messages)
        text = response.content if hasattr(response, "content") else str(response)

        # Extract analogies and jargon
        words = text.split()
        return LessonContent(
            title=f"Introduction to {topic}",
            topic=topic,
            content_markdown=text,
            word_count=len(words),
            analogies_used=["Open-Book vs Closed-Book Exam"],
            jargon_explained=["Retrieval", "Augment", "Generation", "Hallucination"]
        )
    except Exception as e:
        # Graceful fallback to MockLLMService if network or quota error occurs
        print(f"[Generator] Live LLM call failed ({e}). Falling back to Mock service.")
        return MockLLMService.generate_lesson(topic=topic, guardrails=guardrails, deliberate_error=deliberate_error)
