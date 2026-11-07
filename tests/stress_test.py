"""
Stress testing script: Runs a battery of diverse, random real-world words
through the generator and evaluator pipeline to verify groundedness and zero hallucinations.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import config
config.provider = "gemini"

from src.graph import content_workflow

test_words = [
    "biryani",
    "kangaroo",
    "mosquito",
    "black hole",
    "cricket bat",
    "toothbrush",
    "jugaad",
    "banana"
]

print("=" * 60)
print(f"RUNNING STRESS TEST ON {len(test_words)} RANDOM WORDS VIA GOOGLE GEMINI")
print("=" * 60)

for idx, word in enumerate(test_words, 1):
    print(f"\n[{idx}/{len(test_words)}] Testing Topic: '{word}'...")
    state = {
        "topic": word,
        "iteration": 0,
        "max_retries": 2,
        "current_lesson": None,
        "latest_evaluation": None,
        "history": [],
        "rejection_log": [],
        "deliberate_error": None,
        "status": "starting",
        "learned_guardrails": []
    }
    
    try:
        final_state = content_workflow.invoke(state)
        lesson = final_state.get("current_lesson")
        eval_rep = final_state.get("latest_evaluation")
        
        status_symbol = "✅ PASS" if eval_rep and eval_rep.overall_passed else "❌ FAIL"
        print(f"  Result: {status_symbol} (Completed in {final_state['iteration'] + 1} attempt(s))")
        if lesson:
            # Print first 2 lines
            lines = [l.strip() for l in lesson.content_markdown.split('\n') if l.strip()]
            preview = lines[0] if lines else "No content"
            print(f"  Lesson Header: {preview}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 60)
print("STRESS TEST COMPLETED!")
print("=" * 60)
