# How to Run DevGuard

## ⚠️ IMPORTANT: Always Use Virtual Environment

**DO NOT use:** `streamlit run app.py` (uses system Python)

**USE THIS INSTEAD:**
```bash
cd /Users/vishwapandiyan/Desktop/Devgaurd
source venv/bin/activate
python3 -m streamlit run app.py
```

## Alternative: Use the Startup Script

```bash
cd /Users/vishwapandiyan/Desktop/Devgaurd
./run.sh
```

## Why?

- System Python doesn't have the required packages (langchain-google-genai, etc.)
- Virtual environment has all dependencies installed
- Using `python3 -m streamlit` ensures you use the venv's Python

## Verify You're Using Venv

```bash
which python3
# Should show: .../Devgaurd/venv/bin/python3
# NOT: /Library/Frameworks/Python.framework/...
```

