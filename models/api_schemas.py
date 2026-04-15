"""
Schemas API pour exposer le moteur d'entretien en service HTTP.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    cv: Dict[str, Any]
    job: Dict[str, Any]
    score_matching_initial: Optional[float] = Field(default=0.78)


class AnswerInterviewRequest(BaseModel):
    answer: str


class InterviewStateSummary(BaseModel):
    current_axis: Optional[str] = None
    question_count: int
    covered_axes: int
    total_axes: int
    score_entretien: float


class InterviewResultPayload(BaseModel):
    candidat: Dict[str, Any]
    poste: Dict[str, Any]
    scoring: Dict[str, Any]
    evaluation: Dict[str, Any]
    entretien: Dict[str, Any]


class StartInterviewResponse(BaseModel):
    session_id: str
    status: Literal["in_progress"]
    question: str
    summary: InterviewStateSummary


class AnswerInterviewResponse(BaseModel):
    session_id: str
    status: Literal["in_progress", "completed"]
    question: Optional[str] = None
    result: Optional[InterviewResultPayload] = None
    summary: InterviewStateSummary


class SessionStatusResponse(BaseModel):
    session_id: str
    status: Literal["in_progress", "completed", "not_found"]
    summary: Optional[InterviewStateSummary] = None
    result: Optional[InterviewResultPayload] = None


class HealthResponse(BaseModel):
    status: str
