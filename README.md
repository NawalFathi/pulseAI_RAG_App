<div align="center">

# ⚡ PulseAI

### Website Research API

**Turn public webpages into clear, source-grounded answers.**

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)

**Ingest a page** &nbsp; → &nbsp; **Ask a question** &nbsp; → &nbsp;
**Get an answer grounded in its content**

</div>

PulseAI helps InsightIQ analysts research public webpages without manually
reading every page. It stores searchable page content and answers questions
using relevant excerpts—not the model's general knowledge. When the page
doesn't support an answer, PulseAI responds:
**“This information was not found on the website.”**

> **Scope:** Ingestion processes one submitted webpage, not every page on its
> domain.

## ✨ At a glance

|        Ingest         |        Ask         |                      Explore                       |
| :-------------------: | :----------------: | :------------------------------------------------: |
| `POST /api/v1/ingest` | `POST /api/v1/ask` | [Interactive API docs](http://127.0.0.1:8000/docs) |

## 🔄 How it works

|       Step       | What happens                                                 |
| :--------------: | ------------------------------------------------------------ |
| **1 · Extract**  | Playwright opens a public webpage; readable text is cleaned. |
| **2 · Prepare**  | Text is split into overlapping chunks and embedded.          |
|  **3 · Store**   | PostgreSQL with pgvector persists the page and vectors.      |
| **4 · Retrieve** | A question finds relevant chunks for its `ingest_id`.        |
|  **5 · Answer**  | The LLM responds using retrieved page excerpts as context.   |

## 🧰 Tech stack

`Python 3.14` · `FastAPI` · `Playwright` · `Beautiful Soup` ·
`OpenAI API` · `PostgreSQL` · `pgvector` · `Pytest`

## 🚀 Run locally (Windows)

**You’ll need:** Python 3.14, Docker Desktop, and an OpenAI API key with
access to the configured models. OpenAI API usage may incur charges.

### 1. Install

From the repository root, run in PowerShell:

```powershell
Set-Location .\pulseAI_App
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
```

### 2. Configure

Edit `.env` with your OpenAI API key, enabled chat model, and database
password. `DB_PASSWORD` and the password in `DATABASE_URL` must match.
**Never commit or share `.env`.**

### 3. Start

```powershell
docker compose up -d
python -m app.models.init_db
python -m uvicorn app.main:app --reload
```

The initialization command enables the PostgreSQL `vector` extension and
creates the application tables. Visit **http://127.0.0.1:8000/docs** to try
the API.

## 📡 API examples

Ingest the page first, then use its returned `ingest_id` to ask questions.

<details>
<summary><strong>1. Ingest a webpage · POST /api/v1/ingest</strong></summary>

**Request**

```json
{
  "url": "https://www.flipkart.com/"
}
```

**Response · 200 OK**

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

Submitting the same normalized URL again reuses its existing ID.

</details>

<details>
<summary><strong>2. Ask a question · POST /api/v1/ask</strong></summary>

**Request**

```json
{
  "ingest_id": "7411b201-95a2-46bf-9291-e62190013880",
  "question": "what service does this website provide"
}
```

**Response · 200 OK**

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

Actual answer wording depends on the page content and model response.

</details>

Errors follow a consistent envelope:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "A concise description of the error."
  }
}
```

## 🧪 Tests

From `pulseAI_App`, with the virtual environment active:

```powershell
python -m pytest -v
```
