# 🎓 Autonomous Lesson Generator: Self-Evaluating Content System

> **GenAI Engineer - Content Systems | Agentic AI Project**  
> An autonomous, self-evaluating agentic system that generates beginner educational content, judges its own quality against a strict 6-checkpoint hard pass/fail rubric, self-evolves its guardrails through persistent memory, and auto-regenerates rejected content until it is cleared to ship.

---

## 🌟 Quick Links to Deliverables

- 📄 **Final Lesson Document:** [`FINAL_LESSON_DOCUMENT.md`](./FINAL_LESSON_DOCUMENT.md) (Complete, publication-ready RAG lesson for Google Doc / Notion submission)
- ⚠️ **Rejection & Self-Correction Log:** [`REJECTION_LOG.md`](./REJECTION_LOG.md) (Full audit logs showing failure reasons, offending quotes, and corrective changes)
- 🏗️ **Technical Architecture & Specifications:** [`ARCHITECTURE.md`](./ARCHITECTURE.md) (Detailed system design rationale, state machine specs, and trade-offs)

---

## 🎯 The Core Problem & Target Learner Persona

Standard LLM generation pipelines rely on "one clever prompt" that frequently drifts into academic jargon, leaves technical terms unexplained, or hallucinates architectural facts. In an autonomous content system, content must clear a rigorous quality bar **before any human ever sees it**.

### Target Audience Profile:
- **Learner:** 12th-grade graduate from India (CBSE / State Board).
- **Background:** Non-English-medium schooling (e.g. Hindi, Tamil, Telugu, Marathi medium); limited English vocabulary.
- **Ambition:** Motivated to break into AI and kickstart a high-demand tech career.
- **Pedagogical Requirement:** Short sentences (<18 words), relatable Indian everyday analogies (Open-Book vs Closed-Book Exam, Kirana shop ledger), and **zero unexplained jargon**.

---

## 🏗️ System Architecture (LangGraph State Machine)

The engine is built on **LangGraph**, orchestrating a cyclic state machine with bounded retries ($\le 2$) to guarantee strict termination:

```mermaid
flowchart TD
    Start([Input Topic: 'Introduction to RAG']) --> MemFetch[1. Fetch Active Evolved Guardrails<br/>from Memory]
    MemFetch --> GenNode[2. Generator Agent<br/>Persona-Tuned Draft Creation]
    GenNode --> EvalNode[3. Evaluator Agent<br/>6 Hard Pass/Fail Rubric Gates]
    
    EvalNode --> Decision{All 6 Checks<br/>Passed?}
    
    Decision -- YES (PASS) --> SuccessNode[4. Success Node<br/>Ship Lesson to Production]
    
    Decision -- NO (FAIL) --> RetryGate{Retries < Max (2)?}
    
    RetryGate -- YES --> RegenNode[5. Regenerator Agent<br/>Targeted Error Remediation]
    RegenNode --> EvalNode
    
    RetryGate -- NO --> MaxRetriesNode[6. Max Retries Exceeded<br/>Flag for Human Review]

    EvalNode -.->|Update Mistake Counts| MemStore[(Persistent Memory<br/>data/memory.json)]
    MemStore -.->|Derive Sharpened Rules| MemFetch
    
    SuccessNode --> FinalArtifacts([Final Lesson + Audit Logs])
    MaxRetriesNode --> FinalArtifacts
```

---

## 📐 The 6 Hard Pass/Fail Rubric Checkpoints

We enforce a **Hard Pass/Fail** standard with **no partial credit**. In education, a 95% average score is broken if the remaining 5% teaches false facts or introduces unexplained advanced calculus.

| # | Checkpoint Identifier | Hard Pass Criterion | Fatal Failure Condition |
|---|---|---|---|
| **1** | `accurate_and_grounded` | Accurately frames RAG as inference-time retrieval into prompt. | Claims RAG retrains, fine-tunes, or modifies model weights. |
| **2** | `beginner_friendly_language` | Simple English, sentences $<18$ words, warm encouraging tone. | Dense academic prose, long rambling sentences ($>22$ words). |
| **3** | `teaches_by_example` | Features relatable Indian analogy (Open-Book vs Closed-Book Exam). | Abstract-only explanation without any real-world mental model. |
| **4** | `no_unexplained_jargon` | Every tech term translated into plain English immediately. | Dropping *Vector DB*, *Embeddings*, or *Hallucination* without definitions. |
| **5** | `covers_key_points` | Covers What it is, Why it matters, and 3-step How loop (Retrieve, Augment, Generate). | Omits any of the three fundamental pillars. |
| **6** | `coherent_teaching_flow` | Logical progression: Hook $\to$ Problem $\to$ Analogy $\to$ 3 Steps $\to$ Career $\to$ Quiz. | Jumps directly to architecture or code before establishing intuition. |

---

## 🧠 Self-Evolving Memory System

The system persists execution records across runs in `data/memory.json`:
1. **Recurring Mistake Tracking:** Tracks cumulative failure frequencies for each rubric dimension.
2. **Dynamic Guardrail Synthesis:** When a failure threshold is triggered, the `MemoryManager` dynamically generates a strict constraint:
   > `STRICT SHARPENED GUARDRAIL (From Memory): Never introduce 'Vector Database' without immediately describing it as 'a smart digital filing cabinet'.`
3. **Continuous Prompt Hardening:** Future generations automatically inherit these rules, preventing regression across topics.

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.10+ installed.

### 2. Clone and Setup
```bash
# Navigate to the project directory
cd autonomous-lesson-generator

# (Optional) Setup virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. API Keys Configuration (Optional)
The system runs **out of the box** using a High-Fidelity Mock Simulator (zero cost, zero API keys required). To connect live models:
```bash
copy .env.example .env
```
Edit `.env`:
```ini
LLM_PROVIDER=gemini        # "gemini" | "openai" | "mock"
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-flash-lite-latest
```

---

## 🖥️ Running the System

### Option A: Interactive Streamlit Web Dashboard (Recommended for Demos)
```bash
streamlit run app.py
```
- Real-time visual LangGraph state tracking.
- Toggle between Clean Runs and Deliberate Error modes (`jargon_bomb`, `missing_analogy`, `hallucination`).
- Side-by-side inspect of Rubric badges, Rejection Log, and Evolved Memory.

### Option B: Rich Terminal CLI
```bash
# 1. Clean Run
python cli.py --topic "Introduction to RAG"

# 2. Deliberate Error Mode (Evaluator catches error & auto-remediates)
python cli.py --topic "Introduction to RAG" --deliberate-error jargon_bomb
```

### Option C: Automated Unit & Deliberate Error Test Suite
```bash
python -m unittest discover tests
```
Runs 5 automated integration tests verifying:
- Clean pipeline execution & rubric clearance.
- Bounded loop termination on max retries.
- Catching deliberate errors (`jargon_bomb`, `missing_analogy`, `hallucination`).
- Memory persistence and self-evolving guardrail updates.

---

## 🚨 Deliberate Error Catching & Auto-Remediation

To verify that the Evaluator acts as a true autonomous gatekeeper:
```bash
python cli.py --topic "Introduction to RAG" --deliberate-error jargon_bomb
```

### What Happens:
1. **Attempt #0:** Generator outputs a draft with terms like *"Euclidean latent space with cosine similarity indices"*.
2. **Evaluator Audit:** Catches the failure, flags `no_unexplained_jargon` and `beginner_friendly_language`, quotes the violating phrase, and rejects the draft.
3. **Rejection Log:** Records the failure reason and remediation instructions in `data/rejection_log.json`.
4. **Regenerator Node:** Takes the critique, strips the jargon, adds the *"Open-Book Exam"* analogy, and re-submits.
5. **Attempt #1:** Evaluator audits the revision against all 6 checkpoints $\to$ **ALL PASS (SHIPPED)**.

---

## 📁 Repository Directory Structure

```
autonomous-lesson-generator/
├── .env.example                   # Environment configuration template
├── README.md                      # Primary project overview & documentation
├── ARCHITECTURE.md                # System specifications & design rationale
├── FINAL_LESSON_DOCUMENT.md       # Final created RAG lesson content
├── REJECTION_LOG.md               # Audit log of rejections & self-corrections
├── requirements.txt               # Dependencies
├── app.py                         # Streamlit interactive web dashboard
├── cli.py                         # Rich terminal CLI runner
├── data/
│   ├── memory.json                # Cross-run persistent memory & evolved rules
│   └── rejection_log.json         # Rejection log audit trail
├── tests/
│   ├── __init__.py
│   ├── test_workflow.py           # Clean pipeline & termination unit tests
│   └── test_deliberate_errors.py  # Automated deliberate error catching tests
└── src/
    ├── __init__.py
    ├── config.py                  # Persona & system configuration
    ├── models.py                  # Pydantic data schemas & state models
    ├── rubric.py                  # 6 Hard pass/fail rubric definitions & heuristics
    ├── memory.py                  # Memory manager & self-evolving rule synthesizer
    ├── llm.py                     # Multi-provider LLM adapter (Gemini, OpenAI, Mock)
    ├── graph.py                   # LangGraph StateGraph workflow definition
    └── agents/
        ├── __init__.py
        ├── generator.py           # Lesson generator agent
        ├── evaluator.py           # Rubric evaluator agent
        └── regenerator.py         # Reflection & targeted remediation agent
```

---

## ⚖️ Key Engineering Trade-offs & Decisions

1. **Why LangGraph over linear chains?**  
   Linear pipelines cannot handle autonomous quality failures. LangGraph provides an explicit cyclic state machine with conditional branching, audit snapshots, and loop termination guarantees.
2. **Why Hard Pass/Fail over weighted float scores?**  
   Continuous numerical scores mask critical failures. An average score of 92% is unacceptable if the remaining 8% contains an AI hallucination or introduces advanced linear algebra to a 12th-grade beginner.
3. **Why Bounded Retries (Max 2)?**  
   Unbounded agent loops can cause infinite execution loops and runaway API costs. Max 2 retries gives the system two opportunities to self-correct while guaranteeing deterministic termination.
4. **Why Multi-Layered Evaluation (Heuristics + LLM)?**  
   Deterministic checks (sentence length, word count, regex patterns) provide fast, un-hackable baselines that prevent LLM evaluator complacency.
