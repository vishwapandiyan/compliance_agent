#!/bin/bash
# DevGuard Startup Script - Ensures venv is used

cd "$(dirname "$0")"
source venv/bin/activate
python3 -m streamlit run app.py

