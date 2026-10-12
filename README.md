# PulseAI Website Research API

PulseAI is a FastAPI backend for InsightIQ, a market research firm whose
analysts need to research public webpages without manually reading each page.
An analyst submits a webpage URL, then asks questions about that page and
receives an answer based on its extracted content.

The API extracts readable text from the submitted public webpage, divides it
into overlapping chunks, creates vector embeddings, and persists the website
and its chunks in PostgreSQL with pgvector. Analysts can query the saved
content repeatedly using its `ingest_id`, without ingesting the same
normalized URL again.

This project ingests one submitted webpage per URL; it does not crawl every
page on the website's domain.

## How the solution works

1. **Ingest:** `POST /api/v1/ingest` validates and normalizes the URL, checks
   whether it has already been ingested, extracts readable page text, creates
   overlapping chunks and embeddings, and saves the result.
2. **Retrieve:** `POST /api/v1/ask` uses the `ingest_id` and question to
   generate a question embedding and search that website's stored chunks by
   cosine similarity.
3. **Answer:** The most relevant chunks are sent to the language model with
   instructions to answer only from those excerpts. If no relevant excerpts
   are found or the model indicates the content is insufficient, the API
   returns `This information was not found on the website`.
4. **Respond and log:** Successful responses and errors use a consistent
   JSON envelope. Ingestion, retrieval, model calls, and failures are logged.

The grounding prompt and relevance threshold are safeguards, not a formal
guarantee that a language model will never make an unsupported claim. Review
answers before relying on them for high-impact decisions.

## Features

- Scrape a public HTTP or HTTPS webpage.
- Clean and split extracted text into overlapping chunks.
- Generate OpenAI embeddings and store them in PostgreSQL/pgvector.
- Retrieve relevant chunks using cosine similarity.
- Generate answers grounded in retrieved website content.
- Reuse the existing `ingest_id` when the same normalized URL is ingested
  again.
- Return consistent success and error response formats.

## Requirements

- Python 3.14 (the project has been tested with Python 3.14.6).
- Docker Desktop with Docker Compose.
- An OpenAI API key with access to the configured embedding and chat models
  and available API quota.
- Internet access for scraping websites and calling the OpenAI API.

OpenAI API usage is separate from a ChatGPT subscription and may incur charges.
This project does not provide free API credits.

## Setup on Windows

Run all commands from the project directory containing this README,
`requirements.txt`, and `docker-compose.yml`.

### 1. Create a virtual environment and install dependencies

In PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### 2. Configure the environment

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Edit `.env`. Set a real OpenAI API key, a chat model available to your API
account, and a database password. Use the same password in `DB_PASSWORD` and
`DATABASE_URL`:

```dotenv
DATABASE_URL=postgresql+psycopg2://postgres:<DB_PASSWORD>@127.0.0.1:5433/pulseai
DB_PASSWORD=<choose-a-local-database-password>
OPENAI_API_KEY=<your-openai-api-key>
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=<an-enabled-responses-api-model>
EMBEDDING_DIMENSION=1536
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=5
SIMILARITY_THRESHOLD=0.20
SCRAPE_TIMEOUT=30000
LOG_LEVEL=INFO
```

`EMBEDDING_DIMENSION` must match the vectors returned by the embedding model.
Changing it for an existing database requires migrating or recreating the
`content_chunks.embedding` column and regenerating the stored vectors. Do not
commit `.env` or share its credentials.

### 3. Start PostgreSQL

The Compose file publishes PostgreSQL on port `5433` on your computer and
stores database files in the `postgres_data` Docker volume:

```powershell
docker compose up -d
docker compose ps
```

Wait for PostgreSQL to become healthy before continuing.

### 4. Initialize the database

```powershell
python -m app.models.init_db
```

This enables the pgvector extension and creates the application's tables.

### 5. Start the API

```powershell
python -m uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Interactive API documentation is
available at `http://127.0.0.1:8000/docs`.

## API

All application endpoints use the `/api/v1` prefix.

### Ingest a webpage

```http
POST /api/v1/ingest
Content-Type: application/json
```

Request:

```json
{
  "url": "https://example.com/"
}
```

Successful response:

```json
{
  "success": true,
  "data": {
    "ingest_id": "generated-ingest-id",
    "url": "https://example.com/",
    "message": "Website ingested successfully"
  }
}
```

Save the returned `ingest_id` for retrieval and question answering. If the
same normalized URL was already ingested, the existing ID is returned and the
page is not ingested again.

### Ask a question

```http
POST /api/v1/ask
Content-Type: application/json
```

Request:

```json
{
  "ingest_id": "generated-ingest-id",
  "question": "What products does this company offer?"
}
```

Successful response:

```json
{
  "success": true,
  "data": {
    "ingest_id": "generated-ingest-id",
    "question": "What products does this company offer?",
    "answer": "Based on the website content, the company offers the products described on the page."
  }
}
```

The ID, question, and answer in a real response depend on the request and
ingested page; the example values above are illustrative. If retrieval finds
no relevant content, the answer is exactly:

```text
This information was not found on the website
```

Errors use this response structure:

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

## Example PowerShell workflow

With the API running in another terminal:

```powershell
$ingestion = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/ingest" `
  -ContentType "application/json" `
  -Body (@{ url = "https://example.com/" } | ConvertTo-Json)

$ingestId = $ingestion.data.ingest_id

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/ask" `
  -ContentType "application/json" `
  -Body (@{
    ingest_id = $ingestId
    question = "What does this website describe?"
  } | ConvertTo-Json)
```

## Configuration reference

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy connection URL for PostgreSQL. |
| `DB_PASSWORD` | Password used by Docker Compose to initialize PostgreSQL. |
| `OPENAI_API_KEY` | Credential for embeddings and answer generation. |
| `OPENAI_EMBEDDING_MODEL` | OpenAI model used to embed chunks and questions. |
| `OPENAI_CHAT_MODEL` | Model used by the OpenAI Responses API. |
| `EMBEDDING_DIMENSION` | Vector size; must match the embedding model. |
| `CHUNK_SIZE` | Maximum chunk length in characters. |
| `CHUNK_OVERLAP` | Number of overlapping characters between chunks. |
| `TOP_K` | Maximum number of similar chunks to consider. |
| `SIMILARITY_THRESHOLD` | Minimum cosine similarity for a chunk to be included. |
| `SCRAPE_TIMEOUT` | Browser navigation timeout in milliseconds. |
| `LOG_LEVEL` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |

Environment variables take precedence over values in `.env`.
`CHUNK_OVERLAP` must be smaller than `CHUNK_SIZE`.

## Tests

Run the tests from the project directory with the virtual environment active:

```powershell
python -m pytest -v
```

The tests use local configuration defaults and mock external services where
appropriate; live OpenAI calls and scraping may require network access and API
quota.

## Scope and operational notes

- The scraper processes the submitted webpage URL; it does not crawl every
  page on the site's domain.
- Some JavaScript-heavy websites or sites that block automated browsing may
  provide incomplete or inaccessible text.
- Scraping is limited to public HTTP(S) destinations; localhost and
  non-public network addresses are rejected.
- Answers are generated using retrieved website excerpts and explicit
  grounding instructions. This reduces unsupported answers but cannot
  mathematically guarantee that a language model will never make an error.
- The project does not include user authentication or authorization. Do not
  expose the development API directly to the public internet.
- PostgreSQL data persists in the `postgres_data` Docker volume. Avoid
  removing that volume if ingested data must be retained.

## Professional submission checklist

Before sharing or submitting this project:

1. **Keep secrets private.** Never include `.env`, real API keys, database
   passwords, or production data. Submit `.env.example` with placeholder
   values so reviewers can configure their own environment.
2. **Verify a clean setup.** Follow the Windows setup steps above from a fresh
   virtual environment, initialize PostgreSQL, and confirm that `/docs` opens.
3. **Run and report tests.** Run `python -m pytest -v`; include the actual
   result in your submission notes rather than claiming unrun checks passed.
4. **Demonstrate both endpoints.** Show an ingestion request, save its
   `ingest_id`, then use that ID in an ask request. Include one representative
   success response and, if requested, an error response.
5. **Explain scope and assumptions.** State that ingestion handles one
   publicly accessible webpage at a time, describe external requirements
   (PostgreSQL/pgvector, Playwright Chromium, and an enabled OpenAI API key),
   and note known limitations such as sites that block automated browsing.
6. **Submit a reviewable source package.** For a Git-based submission, push
   the source, tests, README, dependency manifest, and `.env.example` to a
   branch, then open a pull request with a concise summary, setup/test steps,
   and any known limitations. For a file-based submission, provide the
   project source as a ZIP with the same files and exclude `.env`, virtual
   environments, caches, and generated secrets.
