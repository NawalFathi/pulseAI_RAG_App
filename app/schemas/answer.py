
from pydantic import BaseModel


class AnswerData(BaseModel):
    ingest_id: str
    question: str
    answer: str


class AskResponse(BaseModel):
    success: bool = True
    data: AnswerData
