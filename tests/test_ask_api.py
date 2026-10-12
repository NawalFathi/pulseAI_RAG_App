
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.api.dependencies import (
    get_llm_service,
    get_retrieval_service,
)
from app.schemas.retrieval import RetrievedChunk
from app.services.llm_service import FALLBACK_ANSWER


INGEST_ID = "12345678-1234-1234-1234-123456789012"


class FakeRetrievalService:
    async def retrieve(self, db, ingest_id, question):
        """Return a fixed relevant chunk without accessing external services."""

        assert isinstance(ingest_id, str)
        return [
            RetrievedChunk(
                chunk_id=1,
                chunk_index=0,
                content=(
                    "The company provides market research "
                    "and data analysis services."
                ),
                similarity=0.88,
            )
        ]


class FakeLLMService:
    async def generate_answer(self, question, chunks):
        """Return a deterministic answer for API response tests."""

        return (
            "Based on the website content, the company provides market "
            "research and data analysis services."
        )


class FakeFallbackLLMService:
    async def generate_answer(self, question, chunks):
        """Return the standard fallback answer for unsupported questions."""

        return FALLBACK_ANSWER


@pytest.fixture
def override_services():
    """Replace API services with test doubles for the duration of a test."""

    app.dependency_overrides[get_retrieval_service] = (
        lambda: FakeRetrievalService()
    )
    app.dependency_overrides[get_llm_service] = (
        lambda: FakeLLMService()
    )

    yield

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ask_endpoint_success(override_services):
    """Return a successful answer with the requested ingest ID and question."""

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/ask",
            json={
                "ingest_id": INGEST_ID,
                "question": "What services does the company provide?",
            },
        )

    assert response.status_code == 200

    body = response.json()
    assert body == {
        "success": True,
        "data": {
            "ingest_id": INGEST_ID,
            "question": "What services does the company provide?",
            "answer": (
                "Based on the website content, the company provides market "
                "research and data analysis services."
            ),
        },
    }


class FakeNotFoundRetrievalService:
    async def retrieve(self, db, ingest_id, question):
        """Simulate retrieval for an ingest ID that does not exist."""

        from app.services.retrieval_service import WebsiteNotFoundError

        raise WebsiteNotFoundError("No website found.")


@pytest.mark.asyncio
async def test_ask_endpoint_fallback(override_services):
    """Return the configured fallback when the LLM cannot support an answer."""

    app.dependency_overrides[get_llm_service] = (
        lambda: FakeFallbackLLMService()
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/ask",
            json={
                "ingest_id": INGEST_ID,
                "question": "What is the owner's favorite color?",
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["answer"] == FALLBACK_ANSWER


@pytest.mark.asyncio
async def test_unknown_ingest_returns_standard_error_envelope(override_services):
    """Map a missing website to the standard not-found error response."""

    app.dependency_overrides[get_retrieval_service] = (
        lambda: FakeNotFoundRetrievalService()
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/ask",
            json={
                "ingest_id": INGEST_ID,
                "question": "What does the website do?",
            },
        )

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "data": None,
        "error": {
            "code": "INGEST_NOT_FOUND",
            "message": "No ingested website was found for the supplied ingest_id.",
        },
    }


@pytest.mark.asyncio
async def test_invalid_request_returns_standard_error_envelope():
    """Reject a malformed ingest ID using the standard validation envelope."""

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/ask",
            json={"ingest_id": "not-a-uuid", "question": "Question"},
        )

    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "data": None,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "The request contains invalid input.",
        },
    }
