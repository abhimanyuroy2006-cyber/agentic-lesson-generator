"""
Configuration module for the Self-Evaluating Lesson Content Generator.
"""
from dataclasses import dataclass, field
import os
from pathlib import Path
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TargetPersona:
    """Explicit learner profile definition."""
    name: str = "Pooja / Rahul (12th-grade Indian Graduate)"
    education_level: str = "Class 12 Pass (CBSE / State Board, non-English-medium background)"
    english_proficiency: str = "Basic / Limited English vocabulary; prefers simple everyday words"
    career_goal: str = "Wants to understand modern AI and kickstart a high-demand tech/AI career"
    pedagogical_needs: list = field(default_factory=lambda: [
        "Relatable Indian everyday analogies (school exams, kirana store, mobile apps, library)",
        "Short, punchy sentences (under 18 words on average)",
        "Zero unexplained jargon (every tech term must have a 1-line plain-English meaning first)",
        "Encouraging, friendly, respectful tone (no intimidating academic jargon)",
        "Step-by-step visual mental models before technical names",
    ])


@dataclass
class SystemConfig:
    """Core runtime configuration."""
    provider: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    max_retries: int = int(os.getenv("MAX_RETRIES", "2"))
    memory_path: Path = Path(os.getenv("PERSISTENT_MEMORY_PATH", str(DATA_DIR / "memory.json")))
    rejection_log_path: Path = Path(os.getenv("REJECTION_LOG_PATH", str(DATA_DIR / "rejection_log.json")))
    
    persona: TargetPersona = field(default_factory=TargetPersona)

    def is_api_configured(self) -> bool:
        """Check if an actual API key is present for the selected provider."""
        if self.provider == "gemini":
            return bool(self.gemini_api_key.strip())
        elif self.provider == "openai":
            return bool(self.openai_api_key.strip())
        return False


config = SystemConfig()
