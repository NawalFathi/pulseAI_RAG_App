
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.schemas.retrieval import RetrievedChunk
from app.services.llm_service import (
    FALLBACK_ANSWER,
    LLMService,
)


@pytest.fixture
def llm_service():
    """Provide an LLM service whose network call can be controlled in tests."""

    service = LLMService()
    service.client.responses.create = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_empty_chunks_return_fallback(llm_service):
    """Return the fallback without calling the model when context is absent."""

    answer = await llm_service.generate_answer(
        question="What is the company's revenue?",
        chunks=[],
    )

    assert answer == FALLBACK_ANSWER
    llm_service.client.responses.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_llm_returns_generated_answer(llm_service):
    """Prefix a generated answer with the required grounding statement."""

    llm_service.client.responses.create.return_value = (
        SimpleNamespace(
            output_text="The website offers consulting services."
        )
    )

    chunks = [
        RetrievedChunk(
            chunk_id=1,
            chunk_index=0,
            content="The company offers consulting services.",
            similarity=0.82,
        )
    ]

    answer = await llm_service.generate_answer(
        question="What services does the company offer?",
        chunks=chunks,
    )

    assert answer == (
        "Based on the website content, the website offers consulting services."
    )
    llm_service.client.responses.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_empty_llm_output_returns_fallback(llm_service):
    """Return the fallback when the model response contains no text."""

    llm_service.client.responses.create.return_value = (
        SimpleNamespace(output_text="  ")
    )

    chunks = [
        RetrievedChunk(
            chunk_id=1,
            chunk_index=0,
            content="The company was founded in 2015.",
            similarity=0.75,
        )
    ]

    answer = await llm_service.generate_answer(
        question="When was the company founded?",
        chunks=chunks,
    )

    assert answer == FALLBACK_ANSWER


@pytest.mark.asyncio
async def test_model_fallback_is_returned_without_prefix(llm_service):
    """Preserve the fallback answer instead of adding the grounding prefix."""

    llm_service.client.responses.create.return_value = (
        SimpleNamespace(output_text=f"{FALLBACK_ANSWER}.")
    )
    chunks = [
        RetrievedChunk(
            chunk_id=1,
            chunk_index=0,
            content="The company was founded in 2015.",
            similarity=0.75,
        )
    ]

    answer = await llm_service.generate_answer(
        question="When was the company founded?",
        chunks=chunks,
    )

    assert answer == FALLBACK_ANSWER
