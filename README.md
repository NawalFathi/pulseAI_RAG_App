PulseAI | Website Research API
Turn public webpages into searchable, question-answerable research.

Python FastAPI PostgreSQL

Research the page, not the model's memory.

PulseAI helps InsightIQ analysts turn public webpages into reusable, searchable research. Ingest a page once, ask questions with its ingest_id, and get concise answers grounded in the page's own content—not general model knowledge. If the page does not contain the answer, PulseAI returns: “This information was not found on the website.”

INGEST A WEBPAGE → FIND RELEVANT PASSAGES → GET A GROUNDED ANSWER

PulseAI processes one submitted webpage at a time; it does not crawl every page across a domain.

How it works

Tech stack
Layer Technology
API Python 3.14, FastAPI, Uvicorn
Web extraction Playwright, Beautiful Soup
Retrieval OpenAI embeddings, PostgreSQL, pgvector
Answer generation OpenAI Responses API
Validation and configuration Pydantic, .env
Tests Pytest, pytest-asyncio
Run locally (Windows)
Prerequisites: Python 3.14, Docker Desktop with Docker Compose, and an OpenAI API key with access to the configured models. OpenAI API usage may incur charges.

Run these PowerShell commands from the repository root:

Set-Location .\pulseAI_App
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
Edit pulseAI_App\.env: set your OpenAI API key, an enabled chat model, and your database password. Keep the password in DB_PASSWORD and DATABASE_URL consistent. Never commit .env or share its credentials.

Initialize PostgreSQL and pgvector
Start the PostgreSQL container that includes pgvector:

docker compose up -d
docker compose ps
Wait until PostgreSQL reports healthy, then initialize the vector extension and application tables:

python -m app.models.init_db
This command enables the PostgreSQL vector extension and creates the website and content-chunk tables, including the vector column used for semantic search.

Start the API
python -m uvicorn app.main:app --reload
Open http://127.0.0.1:8000/docs to explore and call the API.

API examples

### 1. Ingest a webpage

`POST /api/v1/ingest`

#### Request body

```json
{
  "url": "https://www.flipkart.com/"
}
```

#### Output — `200 OK`

##### Response body

```json
{
  "success": true,
  "data": {
    "ingest_id": "7411b201-95a2-46bf-9291-e62190013880",
    "url": "https://www.flipkart.com/",
    "message": "Website ingested successfully"
  }
}
```

Save the returned `ingest_id` and use it to ask questions about this webpage.

### 2. Ask a question

`POST /api/v1/ask`

#### Request body

```json
{
  "ingest_id": "7411b201-95a2-46bf-9291-e62190013880",
  "question": "what service does this website provide"
}
```

#### Output — `200 OK`

##### Response body

```json
{
  "success": true,
  "data": {
    "ingest_id": "7411b201-95a2-46bf-9291-e62190013880",
    "question": "what service does this website provide",
    "answer": "Based on the website content, this website provides an online shopping and e-commerce service, offering products across categories such as electronics, fashion, groceries, home furnishings, vehicles, sports equipment, toys, books, and gift cards, with delivery, returns, secure payments, and customer support."
  }
}
```

The examples show a successful API flow. Results depend on the page content
available when it is ingested. If no relevant content supports an answer, the
API returns `This information was not found on the website`. Re-ingesting the
same normalized URL returns the existing ID rather than scraping again.

Tests
From pulseAI_App with the virtual environment active:

python -m pytest -v
