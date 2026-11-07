@echo off
echo =================================================================
echo Starting Autonomous Lesson Generator (Streamlit Dashboard)...
echo =================================================================
cd /d "%~dp0"
start http://localhost:8501
streamlit run app.py --server.port 8501
pause
