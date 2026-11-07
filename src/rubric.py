"""
Rubric definitions and evaluation criteria for the 6 hard pass/fail checkpoints.
"""
from typing import Dict, Any, List
from .models import RubricCheckpointId


RUBRIC_DEFINITIONS: Dict[RubricCheckpointId, Dict[str, Any]] = {
    RubricCheckpointId.ACCURACY_AND_GROUNDEDNESS: {
        "name": "Accurate & Grounded",
        "description": "The technical explanation must be factually correct and avoid hallucinating how RAG works.",
        "pass_criteria": (
            "Accurately explains RAG as retrieving external reference data from a store (database/documents) "
            "and feeding that relevant context into the LLM prompt at inference time, WITHOUT retraining model weights."
        ),
        "fail_criteria": (
            "Claims RAG retrains, fine-tunes, or updates the core LLM weights during queries; "
            "confuses RAG with traditional search engines alone; or provides factually wrong architectural flows."
        )
    },
    RubricCheckpointId.BEGINNER_FRIENDLY_LANGUAGE: {
        "name": "Beginner-Friendly Language",
        "description": "Tailored for a 12th-grade Indian student with non-English-medium schooling and limited vocabulary.",
        "pass_criteria": (
            "Uses simple, everyday English. Average sentence length under 18 words. Avoids passive, convoluted academic "
            "phrasing. Tone is warm, encouraging, and clear."
        ),
        "fail_criteria": (
            "Dense academic prose, long rambling sentences (>22 words on average), high vocabulary barriers "
            "(e.g., 'epistemological', 'ubiquitous', 'syntactic paradigms'), or condescending tone."
        )
    },
    RubricCheckpointId.TEACHES_BY_EXAMPLE: {
        "name": "Teaches by Example",
        "description": "Must anchor abstract concepts to concrete, relatable Indian daily-life analogies.",
        "pass_criteria": (
            "Includes at least one rich, relatable everyday analogy (e.g., Closed-Book Exam vs. Open-Book Exam; "
            "a doctor checking patient case files; or a kirana shopkeeper checking the khata/ledger book) "
            "that directly maps to Retrieve, Augment, and Generate."
        ),
        "fail_criteria": (
            "Explains concepts in purely mathematical or abstract terms without any everyday analogy or real-world mental model."
        )
    },
    RubricCheckpointId.NO_UNEXPLAINED_JARGON: {
        "name": "Clear, No Unexplained Jargon",
        "description": "Every single technical buzzword MUST be translated into plain English immediately when introduced.",
        "pass_criteria": (
            "Any technical term (Embeddings, Vector Database, Hallucination, Retrieval, Context Window, Prompt) "
            "is preceded or immediately followed by a 1-sentence plain-English translation before use."
        ),
        "fail_criteria": (
            "Drops terms like 'vector embeddings', 'cosine similarity', 'semantic search', or 'hallucination' "
            "without defining what they mean in simple plain words first."
        )
    },
    RubricCheckpointId.COVERS_KEY_POINTS: {
        "name": "Covers Key Points",
        "description": "Must thoroughly answer: What is it, Why does it matter, and How does it work.",
        "pass_criteria": (
            "Must explicitly cover: (1) What RAG is (Retrieval-Augmented Generation), "
            "(2) Why it matters (solves outdated knowledge and AI hallucinations/making things up), "
            "(3) How it works (the 3 distinct steps: Retrieve relevant info -> Augment prompt with context -> Generate answer)."
        ),
        "fail_criteria": (
            "Omits any of the three fundamental pillars: What is it, Why it matters, or How the 3-step loop works."
        )
    },
    RubricCheckpointId.COHERENT_TEACHING_FLOW: {
        "name": "Coherent Teaching Flow",
        "description": "Pedagogical progression that builds confidence from zero prior knowledge.",
        "pass_criteria": (
            "Logical progression: (1) Engaging hook & real problem -> (2) Everyday analogy -> (3) How the computer does it "
            "-> (4) Step-by-step example -> (5) Summary & empowering takeaway."
        ),
        "fail_criteria": (
            "Disjointed flow; starts directly with complex architecture diagrams or code before explaining the problem; "
            "jumps back and forth confusingly."
        )
    }
}


def heuristic_language_check(text: str) -> Dict[str, Any]:
    """
    Fast deterministic check on sentence length, word count, and suspicious unexplained keywords.
    Provides grounding signals to complement LLM judgment.
    """
    words = text.split()
    total_words = len(words)
    
    # Split sentences crudely by punctuation
    import re
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sentence_count = max(len(sentences), 1)
    avg_sentence_len = total_words / sentence_count
    
    # Suspicious jargon terms that MUST have explanatory cues nearby
    dangerous_jargon = [
        "cosine similarity", "latent space", "high-dimensional", "embeddings",
        "vector database", "hallucination", "context window", "tokens", "retriever"
    ]
    
    unexplained_flagged = []
    text_lower = text.lower()
    for term in dangerous_jargon:
        if term in text_lower:
            # Check if explanatory patterns exist nearby
            # (e.g. "means", "which is", "like a", "think of", "in simple words")
            explanation_cues = ["means", "meaning", "think of", "like a", "simple words", "simple english", "imagine"]
            has_explanation = any(cue in text_lower for cue in explanation_cues)
            if not has_explanation:
                unexplained_flagged.append(term)

    # Analogy check
    analogy_keywords = ["exam", "book", "library", "doctor", "shopkeeper", "kirana", "ledger", "khata", "student", "paper"]
    has_analogy_keyword = any(kw in text_lower for kw in analogy_keywords)

    return {
        "word_count": total_words,
        "avg_sentence_length": round(avg_sentence_len, 1),
        "suspicious_unexplained_terms": unexplained_flagged,
        "has_analogy_keyword": has_analogy_keyword,
        "is_sentence_length_ok": avg_sentence_len <= 20.0,
    }
