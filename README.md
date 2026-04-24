# Text Summarizer (User Input Only)

This project now performs summarization only for text provided by the user.
It does not download, process, or train on any local dataset.

## Setup

```bash
cd /Users/abhishekgupta/Documents/Text_Summarizer/Text-Summarizer
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Run API

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Run Website

Open this in your browser after server starts:

```text
http://127.0.0.1:8000/
```

### API Usage

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Summarize text:

```bash
curl -X POST http://127.0.0.1:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your long text here...",
    "max_length": 130,
    "min_length": 30
  }'
```

## Run CLI

```bash
python main.py "Your long text here"
```
