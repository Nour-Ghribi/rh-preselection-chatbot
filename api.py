"""
API FastAPI pour exposer le chatbot RH de preselection.
"""

from fastapi import FastAPI, HTTPException

from config.openrouter_config import validate_config
from models.api_schemas import (
    AnswerInterviewRequest,
    AnswerInterviewResponse,
    HealthResponse,
    SessionStatusResponse,
    StartInterviewRequest,
    StartInterviewResponse,
)
from services.interview_service import build_summary, get_session_status, start_interview, submit_answer


app = FastAPI(
    title="Chatbot RH API",
    version="1.0.0",
    description="API de preselection RH basee sur LangGraph, LangChain et OpenRouter.",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/interview/start", response_model=StartInterviewResponse)
def start_interview_endpoint(payload: StartInterviewRequest) -> StartInterviewResponse:
    try:
        validate_config()
        session_id, state = start_interview(
            cv_data=payload.cv,
            job_data=payload.job,
            score_matching_initial=payload.score_matching_initial,
        )
        return StartInterviewResponse(
            session_id=session_id,
            status="in_progress",
            question=state["question_courante"],
            summary=build_summary(state),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/interview/{session_id}/answer", response_model=AnswerInterviewResponse)
def answer_interview_endpoint(session_id: str, payload: AnswerInterviewRequest) -> AnswerInterviewResponse:
    try:
        status, state, result = submit_answer(session_id=session_id, answer=payload.answer)
        return AnswerInterviewResponse(
            session_id=session_id,
            status=status,
            question=state["question_courante"] if status == "in_progress" else None,
            result=result,
            summary=build_summary(state),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/interview/{session_id}", response_model=SessionStatusResponse)
def get_interview_status_endpoint(session_id: str) -> SessionStatusResponse:
    status, state, result = get_session_status(session_id)
    if status == "not_found":
        return SessionStatusResponse(session_id=session_id, status="not_found")
    return SessionStatusResponse(
        session_id=session_id,
        status=status,
        summary=build_summary(state),
        result=result,
    )
