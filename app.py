"""
Streamlit Web Dashboard for the Self-Evaluating Lesson Content Generator.
Interactive UI supporting ANY user topic, live/mock models, deliberate error demonstrations,
and real-time LangGraph multi-agent loop inspection.
"""
import streamlit as st
from datetime import datetime
from pathlib import Path

from src.graph import content_workflow
from src.config import config
from src.memory import memory
from src.models import EvaluationReport, RubricCheckpointId

# Page configuration
st.set_page_config(
    page_title="Autonomous Lesson Generator - Agentic Content System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- Header & Context -----------------
st.title("🎓 Autonomous Lesson Generator: Self-Evaluating Content System")
st.caption("GenAI Engineer - Content Systems | Multi-Agent Loop: Generate ➔ Evaluate (Hard Pass/Fail) ➔ Regenerate")

st.info(
    "🎯 **Target Learner Persona:** Class 12 Indian Graduate (non-English-medium background, limited vocabulary, aspiring AI career). "
    "Every lesson is evaluated against **6 hard pass/fail checkpoints** (zero partial credit) before it is cleared to ship."
)

# ----------------- Sidebar Controls -----------------
with st.sidebar:
    st.header("⚙️ Settings & Engine")
    
    # Auto-detect if Gemini API key is configured
    has_gemini = bool(config.gemini_api_key.strip())
    engine_options = ["Google Gemini (Live AI - Like ChatGPT)", "Dynamic Engine (Offline Fallback)", "OpenAI"]
    default_index = 0 if has_gemini else 1

    provider_choice = st.selectbox(
        "AI Engine / Provider",
        options=engine_options,
        index=default_index,
        help="Google Gemini generates 100% live, accurate lessons for ANY topic in the universe."
    )
    
    if "Gemini" in provider_choice:
        config.provider = "gemini"
        st.success("🟢 Live Gemini AI Connected")
    elif "OpenAI" in provider_choice:
        config.provider = "openai"
        api_key_input = st.text_input("OpenAI API Key", type="password", value=config.openai_api_key)
        if api_key_input:
            config.openai_api_key = api_key_input
    else:
        config.provider = "mock"
        st.warning("⚠️ Running in Offline Mode")

    st.markdown("---")
    st.subheader("🚨 Test Deliberate Error")
    st.caption("Required for the Loom video: showcase the Evaluator catching an intentional error and auto-correcting it.")
    deliberate_error = st.selectbox(
        "Error Injection Mode",
        options=["None (Clean Production Run)", "jargon_bomb", "missing_analogy", "hallucination"],
        index=0,
        help="Injects complex math terms, removes analogies, or introduces false facts to test the evaluator."
    )
    delib_err_val = None if deliberate_error.startswith("None") else deliberate_error

    max_retries = st.slider("Max Retries Allowed", min_value=1, max_value=3, value=2)

    st.markdown("---")
    st.subheader("👤 Learner Profile Guardrails")
    st.markdown(f"**Student:** {config.persona.name}")
    st.markdown(f"**Language:** {config.persona.english_proficiency}")
    st.markdown(f"**Goal:** {config.persona.career_goal}")

# ----------------- Main Topic Input Section -----------------
st.subheader("🔍 What would you like to teach today?")

# Suggested topic chips
col_p1, col_p2, col_p3, col_p4 = st.columns(4)
clicked_topic = None
with col_p1:
    if st.button("📘 Introduction to RAG (Assessment)", use_container_width=True):
        clicked_topic = "Introduction to RAG"
with col_p2:
    if st.button("🚀 XGBoost", use_container_width=True):
        clicked_topic = "XGBoost"
with col_p3:
    if st.button("🧠 Neural Networks", use_container_width=True):
        clicked_topic = "Neural Networks"
with col_p4:
    if st.button("🌳 Decision Trees", use_container_width=True):
        clicked_topic = "Decision Trees"

if clicked_topic:
    st.session_state["active_topic"] = clicked_topic

default_topic = st.session_state.get("active_topic", "Introduction to RAG")

# Form enables execution on BOTH "Enter" key and button click!
with st.form("topic_search_form"):
    topic_input = st.text_input(
        "Enter ANY topic you want (e.g. bath, apple, tiger, gravity, RAG, biryani...):",
        value=default_topic,
        placeholder="Type any word and press Enter..."
    )
    submit_btn = st.form_submit_button("🚀 Generate & Evaluate Lesson", type="primary", use_container_width=True)

# Execute when form is submitted OR when a quick chip was clicked
should_run = submit_btn or (clicked_topic is not None)

if should_run:
    chosen = clicked_topic if clicked_topic else topic_input.strip()
    if not chosen:
        chosen = "Introduction to RAG"
    st.session_state["active_topic"] = chosen

    with st.status(f"⚡ Running Autonomous Content Loop for '{chosen}'...", expanded=True) as status_box:
        st.write(f"🤖 **Generator Agent:** Crafting lesson on '{chosen}' tailored for 12th-grade learner...")
        initial_state = {
            "topic": chosen,
            "iteration": 0,
            "max_retries": max_retries,
            "current_lesson": None,
            "latest_evaluation": None,
            "history": [],
            "rejection_log": [],
            "deliberate_error": delib_err_val,
            "status": "starting",
            "learned_guardrails": memory.get_learned_guardrails()
        }

        final_state = content_workflow.invoke(initial_state)
        st.session_state["final_state"] = final_state

        if final_state.get("status") == "passed":
            status_box.update(label=f"✅ Approved & Published: '{chosen}' cleared all 6 rubric gates!", state="complete", expanded=False)
            st.toast(f"🎉 Lesson on '{chosen}' is ready below!", icon="✅")
        else:
            status_box.update(label=f"⚠️ Evaluator bounded retries completed for '{chosen}'", state="complete", expanded=False)

# If first time loading and nothing generated yet, load RAG preview
if "final_state" not in st.session_state:
    with st.status("Initializing first-run lesson preview...", expanded=False) as init_box:
        initial_state = {
            "topic": "Introduction to RAG",
            "iteration": 0,
            "max_retries": max_retries,
            "current_lesson": None,
            "latest_evaluation": None,
            "history": [],
            "rejection_log": [],
            "deliberate_error": None,
            "status": "starting",
            "learned_guardrails": memory.get_learned_guardrails()
        }
        final_state = content_workflow.invoke(initial_state)
        st.session_state["final_state"] = final_state
        init_box.update(label="✅ Ready!", state="complete")

# ----------------- Results & Inspection Tabs -----------------
state = st.session_state["final_state"]
lesson = state.get("current_lesson")
evaluation = state.get("latest_evaluation")

active_topic_name = st.session_state.get("active_topic", "Introduction to RAG")
l_title = (getattr(lesson, "title", None) or (lesson.get("title") if isinstance(lesson, dict) else None) or active_topic_name)
l_content = (getattr(lesson, "content_markdown", "") or (lesson.get("content_markdown") if isinstance(lesson, dict) else ""))
l_words = (getattr(lesson, "word_count", 0) or (lesson.get("word_count") if isinstance(lesson, dict) else len(l_content.split())))

st.markdown(f"### 📖 Active Lesson: {l_title}")

tab1, tab2, tab3, tab4 = st.tabs([
    "📜 Generated Lesson",
    "⚖️ Rubric Quality Audit (6 Gates)",
    "⚠️ Rejection & Self-Correction Log",
    "🧠 Self-Evolving Memory"
])

# ----- TAB 1: GENERATED LESSON -----
with tab1:
    if l_content:
        meta_c1, meta_c2, meta_c3 = st.columns(3)
        meta_c1.metric("Word Count", f"{l_words} words")
        meta_c2.metric("Target Persona", "12th-Grade Indian Graduate")
        status_label = "✅ SHIPPED" if state.get("status") == "passed" else "❌ RETRIES EXCEEDED"
        meta_c3.metric("Publishing Status", status_label)
        
        st.divider()
        st.markdown(l_content)
        st.divider()

        st.download_button(
            label="📥 Download Lesson as Markdown (.md)",
            data=l_content,
            file_name=f"{active_topic_name.lower().replace(' ', '_')}_lesson.md",
            mime="text/markdown"
        )
    else:
        st.warning("No lesson draft available yet. Click 'Generate & Evaluate Lesson' above!")

# ----- TAB 2: RUBRIC QUALITY AUDIT -----
with tab2:
    st.subheader("Auditing Against the 6 Hard Pass/Fail Gates")
    st.caption("No partial credit: every single checkpoint must strictly PASS for the lesson to clear production.")
    
    for rec in state.get("history", []):
        iter_num = rec["iteration_index"]
        eval_dict = rec["evaluation"]
        eval_report = EvaluationReport.model_validate(eval_dict)
        
        badge_title = "✅ Cleared All Checkpoints" if eval_report.overall_passed else f"❌ Rejected ({len(eval_report.failed_checkpoints)} failed gates)"
        
        with st.expander(f"Attempt #{iter_num}: {badge_title}", expanded=True):
            st.write(f"**Evaluator Verdict:** {eval_report.summary_critique}")
            
            # Display all 6 checkpoints in 2 columns
            c_left, c_right = st.columns(2)
            for idx, cp in enumerate(eval_report.checkpoints):
                col = c_left if idx % 2 == 0 else c_right
                with col:
                    if cp.passed:
                        st.success(f"**PASS:** {cp.name}\n\n*Evidence:* {cp.reason}")
                    else:
                        fail_msg = f"**FAIL:** {cp.name}\n\n*Reason:* {cp.reason}"
                        if cp.violating_quote:
                            fail_msg += f"\n\n**Violating Snippet:** \"{cp.violating_quote}\""
                        if cp.fix_recommendation:
                            fail_msg += f"\n\n**Required Fix:** {cp.fix_recommendation}"
                        st.error(fail_msg)

# ----- TAB 3: REJECTION & REMEDIATION LOG -----
with tab3:
    st.subheader("⚠️ Rejection & Self-Correction Log")
    rej_log = state.get("rejection_log", [])
    
    if rej_log:
        st.write("This log tracks every rejected draft, what rules it broke, and how the Regenerator fixed it.")
        for r in rej_log:
            with st.container():
                st.error(f"**Attempt #{r['attempt_number']} Rejection Summary**")
                st.write(f"**Failed Gates:** `{', '.join(r['failed_checkpoints'])}`")
                st.write(f"**Critique:** {r['why_it_failed']}")
                if r.get("violating_snippets"):
                    st.warning(f"**Offending Snippets Flagged by Evaluator:** {', '.join(r['violating_snippets'])}")
                st.success(f"**Corrective Actions Fed into Regenerator:** {r['corrective_actions']}")
                st.divider()
    else:
        st.info("No rejections occurred on this run! To observe the Evaluator reject and self-correct, select a **Deliberate Error** (like 'jargon_bomb') in the sidebar and click Generate.")

# ----- TAB 4: SELF-EVOLVING MEMORY -----
with tab4:
    st.subheader("🧠 Self-Evolving Memory System")
    st.caption("The system tracks failure patterns across runs and synthesizes persistent guardrails for future prompts.")
    
    mem_data = memory.state
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Total System Runs", mem_data.get("total_runs", 0))
    mc2.metric("Successful Shipments", mem_data.get("successful_runs", 0))
    mc3.metric("Failure Remediations", mem_data.get("failed_runs", 0))

    st.markdown("#### Cumulative Failure Distribution Across Gates")
    counts = mem_data.get("checkpoint_failure_counts", {})
    st.bar_chart(counts)

    st.markdown("#### Active Evolved Guardrails Derived from Mistakes")
    for g in mem_data.get("learned_guardrails", []):
        st.info(f"🛡️ {g}")
