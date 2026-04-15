"""
Service applicatif pour executer l'entretien question par question.
"""

from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Any, Dict, Tuple
from uuid import uuid4

from models.api_schemas import InterviewStateSummary
from models.interview_state import create_initial_state, InterviewState
from models.llm_schemas import CandidateInputModel, JobRequirementModel
from nodes.initialization import initialization_node
from nodes.question_generation import generation_question_node
from nodes.response_analysis import response_analysis_node
from nodes.decision_node import decision_node
from nodes.final_evaluation import final_evaluation_node


_SESSIONS: Dict[str, Dict[str, Any]] = {}
_SESSIONS_LOCK = Lock()


def _validate_inputs(cv_data: Dict[str, Any], job_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    candidate = CandidateInputModel.model_validate(cv_data)
    job = JobRequirementModel.model_validate(job_data)
    return candidate.model_dump(), job.model_dump()


def _resolve_initial_score(request_score: float | None, candidate_data: Dict[str, Any], default_score: float = 0.78) -> float:
    raw_score = request_score if request_score is not None else candidate_data.get("score_matching_init", default_score)
    if raw_score is None:
        return default_score
    try:
        return float(raw_score)
    except (TypeError, ValueError):
        return default_score


def _state_summary(state: InterviewState) -> InterviewStateSummary:
    return InterviewStateSummary(
        current_axis=(state.get("axe_courant") or {}).get("nom"),
        question_count=state["compteur_questions"],
        covered_axes=len(state["axes_couverts"]),
        total_axes=len(state["axes_a_tester"]),
        score_entretien=state["score_entretien"],
    )


def _format_final_result(final_state: InterviewState) -> Dict[str, Any]:
    return {
        "candidat": {
            "nom": final_state["cv_candidat"].get("nom", "Anonyme"),
            "email": final_state["cv_candidat"].get("email", ""),
            "telephone": final_state["cv_candidat"].get("telephone", ""),
        },
        "poste": {
            "titre": final_state["exigences_poste"].get("titre_poste", ""),
            "entreprise": final_state["exigences_poste"].get("entreprise", ""),
        },
        "scoring": {
            "score_matching_initial": final_state["score_matching_init"],
            "score_entretien": final_state["score_entretien"],
            "score_final": final_state["score_final"],
            "variation": round(final_state["score_final"] - final_state["score_matching_init"], 4),
        },
        "evaluation": {
            "recommandation": final_state["recommandation"],
            "points_forts": final_state["points_forts"],
            "points_faibles": final_state["points_faibles"],
            "zones_de_doute": final_state["zones_de_doute"],
            "resume": final_state["resume_entretien"],
        },
        "entretien": {
            "nombre_questions": final_state["compteur_questions"],
            "axes_a_explorer": len(final_state["axes_a_tester"]),
            "axes_couverts": len(final_state["axes_couverts"]),
            "validated_axes": final_state["validated_axes"],
            "weak_axes": final_state["weak_axes"],
            "critical_failures": final_state["critical_failures"],
            "inconsistencies": final_state["inconsistencies"],
            "decision_trace": final_state["decision_trace"],
            "raison_fin": final_state["raison_arret"],
            "historique_qa": final_state["historique_qa"],
        },
    }


def _append_candidate_answer(state: InterviewState, answer: str) -> InterviewState:
    axe_courant = state.get("axe_courant", {})
    nom_axe = axe_courant.get("nom")

    nouvel_echange = {
        "question": state["question_courante"],
        "reponse": answer.strip(),
        "axe": nom_axe,
        "timestamp": datetime.now().isoformat(),
        "analyse": {},
    }

    state["historique_qa"].append(nouvel_echange)
    state["compteur_questions"] += 1

    if nom_axe:
        relances = state["relances_par_axe"].get(nom_axe, 0)
        state["relances_par_axe"][nom_axe] = relances + 1

        action = state.get("derniere_action", "")
        if action in {"clarification", "approfondissement", "reformulation", "verification_incoherence"}:
            state["axis_attempts"].setdefault(
                nom_axe,
                {
                    "clarification": 0,
                    "approfondissement": 0,
                    "reformulation": 0,
                    "verification_incoherence": 0,
                },
            )
            state["axis_attempts"][nom_axe][action] = state["axis_attempts"][nom_axe].get(action, 0) + 1

    return state


def start_interview(cv_data: Dict[str, Any], job_data: Dict[str, Any], score_matching_initial: float | None = None) -> Tuple[str, InterviewState]:
    cv, job = _validate_inputs(cv_data, job_data)
    score = _resolve_initial_score(score_matching_initial, cv)

    state = create_initial_state(cv_candidat=cv, exigences_poste=job, score_matching_init=score)
    state = initialization_node(state)
    state = generation_question_node(state)

    session_id = str(uuid4())
    with _SESSIONS_LOCK:
        _SESSIONS[session_id] = {"state": state, "status": "in_progress", "result": None}

    return session_id, state


def submit_answer(session_id: str, answer: str) -> Tuple[str, InterviewState, Dict[str, Any] | None]:
    with _SESSIONS_LOCK:
        session_data = _SESSIONS.get(session_id)
    if not session_data:
        raise KeyError("Session introuvable")
    if session_data["status"] == "completed":
        return "completed", session_data["state"], session_data["result"]

    if not answer or not answer.strip():
        raise ValueError("La reponse du candidat ne peut pas etre vide.")

    state = session_data["state"]
    state = _append_candidate_answer(state, answer)
    state = response_analysis_node(state)
    state = decision_node(state)

    if state["signal_arret"]:
        state = final_evaluation_node(state)
        result = _format_final_result(state)
        status = "completed"
    else:
        state = generation_question_node(state)
        result = None
        status = "in_progress"

    with _SESSIONS_LOCK:
        _SESSIONS[session_id] = {"state": state, "status": status, "result": result}

    return status, state, result


def get_session_status(session_id: str) -> Tuple[str, InterviewState | None, Dict[str, Any] | None]:
    with _SESSIONS_LOCK:
        session_data = _SESSIONS.get(session_id)
    if not session_data:
        return "not_found", None, None
    return session_data["status"], session_data["state"], session_data["result"]


def build_summary(state: InterviewState) -> InterviewStateSummary:
    return _state_summary(state)
