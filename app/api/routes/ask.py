
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.api.dependencies import (
    get_llm_service,
    get_retrieval_service
)

from app.schemas.answer import AskResponse, AnswerData
from app.schemas.question import QuestionRequest
from app.schemas.response import ErrorResponse
from app.services.llm_service import LLMService
from app.services.retrieval_service import (
    RetrievalService,
    WebsiteNotFoundError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Question Answering"],
)


@router.post(
    "/ask",
    response_model=AskResponse,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
    summary="Answer a question using ingested website content",
    description=(
        "Retrieves relevant website chunks and generates "
        "an answer grounded in the retrieved content. "
        "Returns the configured fallback when the content "
        "does not support an answer."
    ),
)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db),
    retrieval_service: RetrievalService = Depends(
        get_retrieval_service
    ),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Retrieve website evidence and return a grounded answer.

    Invalid questions receive a validation response, missing ingestions
    receive a not-found response, and processing failures are reported as
    an upstream service error.
    """

    question = request.question.strip()
    ingest_id = str(request.ingest_id)

    if not question:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "INVALID_QUESTION",
                    "message": "Question must not be empty.",
                }
            },
        )

    try:
        logger.info("Question answering started | ingest_id=%s", ingest_id)
        chunks = await retrieval_service.retrieve(
            db=db,
            ingest_id=ingest_id,
            question=question,
        )

        answer = await llm_service.generate_answer(
            question=question,
            chunks=chunks,
        )

        logger.info(
            "Question answering completed | ingest_id=%s | chunks=%d",
            ingest_id,
            len(chunks),
        )
        return AskResponse(
            success=True,
            data=AnswerData(
                ingest_id=ingest_id,
                question=question,
                answer=answer,
            ),
        )

    except WebsiteNotFoundError as exc:
        logger.warning("Question rejected | ingest_id=%s | reason=not_found", ingest_id)
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "INGEST_NOT_FOUND",
                    "message": (
                        "No ingested website was found "
                        "for the supplied ingest_id."
                    ),
                }
            },
        ) from exc

    except Exception:
        logger.exception("Question answering failed")
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "code": "QUESTION_ANSWERING_FAILED",
                    "message": (
                        "Unable to process the question "
                        "at this time."
                    ),
                }
            },
        )
