
import os

# Defaults for local tests only.
# Real environment variables take precedence.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/pulseai",
)
os.environ.setdefault(
    "OPENAI_API_KEY",
    "test-api-key",
)
os.environ.setdefault(
    "OPENAI_CHAT_MODEL",
    "test-model",
)
os.environ.setdefault(
    "OPENAI_EMBEDDING_MODEL",
    "text-embedding-3-small",
)
os.environ.setdefault("EMBEDDING_DIMENSION", "1536")
os.environ.setdefault("CHUNK_SIZE", "1000")
os.environ.setdefault("CHUNK_OVERLAP", "200")
os.environ.setdefault("TOP_K", "5")
os.environ.setdefault("SIMILARITY_THRESHOLD", "0.20")
os.environ.setdefault("SCRAPE_TIMEOUT", "30000")
os.environ.setdefault("LOG_LEVEL", "INFO")
