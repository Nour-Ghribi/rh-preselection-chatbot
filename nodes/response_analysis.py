"""
Noeud 4 : ANALYSE_REPONSE

Responsabilites:
- Analyser qualitativement la derniere reponse via LangChain + OpenRouter
- Produire une analyse structuree exploitable par la logique Python
- Stocker l'analyse sans valider prematurement l'axe
"""

from typing import Dict, Any

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from models.interview_state import InterviewState
from models.llm_schemas import ResponseAnalysisOutput
from config.openrouter_config import create_llm_client
from config.prompts import ANALYSIS_SYSTEM_PROMPT, ANALYSIS_HUMAN_PROMPT, format_json_string


def normalize_analysis_output(raw_output: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise l'analyse LLM pour la logique metier."""
    analyse = dict(raw_output or {})
    analyse.setdefault("nature_reponse", "partielle")
    analyse.setdefault("qualite_reponse", "Moyenne")
    analyse.setdefault("signal_metier", "reserve")
    analyse.setdefault("confiance", 0.5)
    analyse.setdefault("besoin_relance", False)
    analyse.setdefault("type_relance", "aucune")
    analyse.setdefault("coherence_cv", "non_verifiable")
    analyse.setdefault("couverture_axe", "partielle")
    analyse.setdefault("evidence_level", "implicite")
    analyse.setdefault("alignment_question", "partiel")
    analyse.setdefault("justification_courte", "")
    return analyse


def response_analysis_node(state: InterviewState) -> InterviewState:
    """Analyse la derniere reponse sans piloter seule la decision."""
    if not state["historique_qa"]:
        raise ValueError("Pas de question/reponse a analyser.")

    derniere_qa = state["historique_qa"][-1]
    question = derniere_qa["question"]
    reponse = derniere_qa["reponse"]
    axe = derniere_qa["axe"]
    axe_courant = state.get("axe_courant") or {}

    parser = JsonOutputParser(pydantic_object=ResponseAnalysisOutput)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ANALYSIS_SYSTEM_PROMPT),
            ("human", ANALYSIS_HUMAN_PROMPT),
        ]
    )
    llm = create_llm_client(max_tokens=700)
    chain = prompt | llm | parser

    payload = {
        "cv_json": format_json_string(state["cv_candidat"]),
        "job_json": format_json_string(state["exigences_poste"]),
        "question": question,
        "axe": axe,
        "axis_importance": axe_courant.get("importance_axe", "important"),
        "reponse": reponse,
        "full_history": format_json_string(state["historique_qa"][:-1]) if len(state["historique_qa"]) > 1 else "Premiere question",
        "format_instructions": parser.get_format_instructions(),
    }

    print(f"\nAnalyse de la reponse sur l'axe : {axe}")

    try:
        analyse = chain.invoke(payload)
        analyse = normalize_analysis_output(analyse)
    except Exception as exc:
        print(f"Erreur OpenRouter pendant l'analyse: {exc}")
        analyse = {
            "nature_reponse": "incomprehensible",
            "qualite_reponse": "Indeterminee",
            "signal_metier": "reserve",
            "confiance": 0.0,
            "besoin_relance": True,
            "type_relance": "clarification",
            "coherence_cv": "non_verifiable",
            "couverture_axe": "insuffisante",
            "evidence_level": "absent",
            "alignment_question": "indirect",
            "justification_courte": "Erreur lors de l'analyse automatique.",
        }

    state["historique_qa"][-1]["analyse"] = analyse

    print(f"Nature     : {analyse.get('nature_reponse', 'N/A')}")
    print(f"Qualite    : {analyse.get('qualite_reponse', 'N/A')}")
    print(f"Signal     : {analyse.get('signal_metier', 'N/A')}")
    print(f"Confiance  : {analyse.get('confiance', 0):.2f}")
    print(f"Relance    : {analyse.get('besoin_relance', False)} ({analyse.get('type_relance', 'aucune')})")

    return state
