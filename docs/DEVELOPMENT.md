# Developer Setup and Testing Guideline

This guide covers the necessary instructions to contribute to and run automated checks on the JARVIS assistant.

---

## 1. Setup Local Environment

### Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install packages
```bash
pip install -r backend/requirements.txt
```

---

## 2. Running Automated Tests

Tests are managed using `pytest`. Ensure that your PYTHONPATH points to the project root directory:
```bash
PYTHONPATH=. pytest backend/tests/
```

---

## 3. Local Web Server

Start the API server locally:
```bash
PYTHONPATH=. uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
And start Vite dev compiler:
```bash
cd frontend
npm install
npm run dev
```
