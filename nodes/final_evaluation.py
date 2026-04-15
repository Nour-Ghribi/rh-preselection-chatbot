"""
Noeud 6 : EVALUATION_FINALE

Responsabilites:
- Analyser l'integralite de l'entretien
- Generer le score final
- Compiler les resultats
- Produire le JSON de sortie final
"""

from typing import Dict, Any

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from models.interview_state import InterviewState
from models.llm_schemas import FinalEvaluationOutput
from config.openrouter_config import create_llm_client
from config.prompts import FINAL_EVALUATION_SYSTEM_PROMPT, FINAL_EVALUATION_HUMAN_PROMPT, format_json_string


def clamp_score(value: float) -> float:
    """Borne un score entre 0.0 et 1.0."""
    return max(0.0, min(1.0, round(value, 4)))


def default_recommendation(score_final: float, critical_failures: list, inconsistencies: list) -> str:
    """Propose une recommandation prudente si le LLM ne renvoie rien d'exploitable."""
    if critical_failures:
        return "A rejeter"
    if inconsistencies or score_final < 0.6:
        return "Dossier a examiner manuellement"
    return "A convoquer"


def normalize_final_evaluation(raw_output: Dict[str, Any], fallback_score: float, state: InterviewState) -> Dict[str, Any]:
    """Normalise l'evaluation finale retournee par le modele."""
    evaluation = dict(raw_output or {})
    final_score = clamp_score(evaluation.get("score_final", fallback_score))
    evaluation["score_final"] = final_score
    evaluation.setdefault("points_forts", [])
    evaluation.setdefault("points_faibles", [])
    evaluation.setdefault("zones_de_doute", [])
    evaluation.setdefault(
        "recommandation",
        default_recommendation(final_score, state["critical_failures"], state["inconsistencies"]),
    )
    evaluation.setdefault("resume", "Resume non disponible")
    return evaluation


def final_evaluation_node(state: InterviewState) -> InterviewState:
    """Compile le resultat final a partir de l'entretien complet."""
    print("\n" + "=" * 60)
    print("EVALUATION FINALE")
    print("=" * 60)

    fallback_score = clamp_score(state["score_matching_init"] + state["score_entretien"])
    parser = JsonOutputParser(pydantic_object=FinalEvaluationOutput)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", FINAL_EVALUATION_SYSTEM_PROMPT),
            ("human", FINAL_EVALUATION_HUMAN_PROMPT),
        ]
    )
    llm = create_llm_client(max_tokens=1600)
    chain = prompt | llm | parser

    payload = {
        "cv_json": format_json_string(state["cv_candidat"]),
        "job_json": format_json_string(state["exigences_poste"]),
        "score_initial": state["score_matching_init"],
        "score_entretien": state["score_entretien"],
        "raison_arret": state["raison_arret"],
        "validated_axes": format_json_string(state["validated_axes"]),
        "weak_axes": format_json_string(state["weak_axes"]),
        "critical_failures": format_json_string(state["critical_failures"]),
        "inconsistencies": format_json_string(state["inconsistencies"]),
        "full_history": format_json_string(state["historique_qa"]),
        "format_instructions": parser.get_format_instructions(),
    }

    try:
        evaluation = chain.invoke(payload)
        evaluation = normalize_final_evaluation(evaluation, fallback_score, state)
    except Exception as exc:
        print(f"Erreur OpenRouter pendant l'evaluation finale: {exc}")
        evaluation = {
            "score_final": fallback_score,
            "points_forts": ["Evaluation heuristique basee sur le matching et l'entretien."],
            "points_faibles": ["Erreur lors de l'evaluation automatique finale."],
            "zones_de_doute": ["Relire l'historique complet de l'entretien."],
            "recommandation": default_recommendation(fallback_score, state["critical_failures"], state["inconsistencies"]),
            "resume": "Evaluation finale derivee des regles Python faute de reponse LLM exploitable.",
        }

    state["score_final"] = clamp_score(evaluation.get("score_final", fallback_score))
    state["points_forts"] = evaluation.get("points_forts", [])
    state["points_faibles"] = evaluation.get("points_faibles", [])
    state["zones_de_doute"] = evaluation.get("zones_de_doute", [])
    state["recommandation"] = evaluation.get("recommandation", default_recommendation(state["score_final"], state["critical_failures"], state["inconsistencies"]))
    state["resume_entretien"] = evaluation.get("resume", "")

    print(f"Score final : {state['score_matching_init']:.2f} + entretien({state['score_entretien']:.2f}) -> {state['score_final']:.2f}")
    print(f"Recommandation : {state['recommandation']}")
    return state
