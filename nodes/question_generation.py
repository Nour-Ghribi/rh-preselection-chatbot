"""
Noeud 2 : GENERATION_QUESTION

Responsabilites:
- Selectionner le prochain axe a explorer
- Generer une question via LangChain + OpenRouter
- Adapter la question au type de relance demande
"""

import re
from typing import Optional, Dict, Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from models.interview_state import InterviewState
from config.openrouter_config import create_llm_client
from config.prompts import QUESTION_SYSTEM_PROMPT, QUESTION_HUMAN_PROMPT, format_json_string, format_list_string


def trouver_prochain_axe(axes_a_tester: list, axes_couverts: list) -> Optional[Dict[str, Any]]:
    """Trouve le prochain axe non encore couvert."""
    for axe in axes_a_tester:
        if axe["nom"] not in axes_couverts:
            return axe
    return None


def build_followup_context(state: InterviewState, axe_courant: Dict[str, Any]) -> str:
    """Construit le contexte de reprise si on reste sur le meme axe."""
    if not state["historique_qa"]:
        return "Question initiale sur cet axe."

    derniere_qa = state["historique_qa"][-1]
    if derniere_qa.get("axe") != axe_courant["nom"]:
        return "Question initiale sur cet axe."

    analyse = derniere_qa.get("analyse", {})
    if not analyse.get("besoin_relance", False):
        return "Question initiale sur cet axe."

    return (
        f"Type de relance demande: {analyse.get('type_relance', 'clarification')}\n"
        f"Derniere reponse du candidat: {derniere_qa.get('reponse', '')}\n"
        f"Nature de reponse detectee: {analyse.get('nature_reponse', 'indeterminee')}\n"
        f"Justification: {analyse.get('justification_courte', 'Approfondir la reponse.')}"
    )


def build_simple_clarification_question(axe_name: str) -> str:
    """Construit une clarification courte et pedagogique."""
    return (
        f"D'accord. Reprenons simplement. "
        f"Avez-vous deja utilise {axe_name} dans un projet concret ? "
        f"Si oui, donnez juste un exemple simple."
    )


def build_simple_reformulation_question(axe_name: str) -> str:
    """Construit une reformulation tres simple quand la question precedente n'etait pas claire."""
    return (
        f"Pas de probleme. Question simple: "
        f"avez-vous deja travaille avec {axe_name} ? "
        f"Repondez juste par oui avec un petit exemple, ou non."
    )


def clean_question(text: str) -> str:
    """Nettoie la question retournee par le modele."""
    question = text.strip()
    question = re.sub(r"^(QUESTION[\s:]*)?", "", question, flags=re.IGNORECASE).strip()
    question = re.sub(r"^[-*]\s*", "", question).strip()
    return question


def generation_question_node(state: InterviewState) -> InterviewState:
    """Genere la prochaine question ou une reprise sur l'axe courant."""
    axe_courant = state.get("axe_courant") or {}
    analyse_precedente = state["historique_qa"][-1]["analyse"] if state["historique_qa"] else {}
    question_mode = "question initiale"

    if not axe_courant:
        axe_courant = trouver_prochain_axe(state["axes_a_tester"], state["axes_couverts"])
        if not axe_courant:
            state["question_courante"] = "Avez-vous autre chose a ajouter ?"
            state["signal_arret"] = True
            state["raison_arret"] = "axes_couverts"
            state["derniere_action"] = "fin"
            return state
        state["axe_courant"] = axe_courant
    elif analyse_precedente.get("besoin_relance"):
        question_mode = analyse_precedente.get("type_relance", "clarification")

    followup_context = build_followup_context(state, axe_courant)
    recent_history = state["historique_qa"][-3:] if state["historique_qa"] else []

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", QUESTION_SYSTEM_PROMPT),
            ("human", QUESTION_HUMAN_PROMPT),
        ]
    )
    llm = create_llm_client(max_tokens=700)
    parser = StrOutputParser()
    chain = prompt | llm | parser

    payload = {
        "cv_json": format_json_string(state["cv_candidat"]),
        "job_json": format_json_string(state["exigences_poste"]),
        "axes_list": format_json_string(state["axes_a_tester"]),
        "covered_axes": format_list_string(state["axes_couverts"]) if state["axes_couverts"] else "Aucun",
        "full_history": format_json_string(recent_history) if recent_history else "Aucun historique",
        "current_axe": axe_courant["nom"],
        "axis_importance": axe_courant.get("importance_axe", "important"),
        "question_mode": question_mode,
        "followup_context": followup_context,
    }

    print(f"\nGeneration Q{state['compteur_questions'] + 1} | axe={axe_courant['nom']}")
    print(f"Mode : {question_mode}")

    try:
        should_force_simple_clarification = (
            question_mode == "clarification"
            and analyse_precedente.get("nature_reponse") == "incomprehensible"
        )
        should_force_simple_reformulation = (
            question_mode == "reformulation"
            and analyse_precedente.get("nature_reponse") == "incomprehensible"
        )

        if should_force_simple_clarification:
            state["question_courante"] = build_simple_clarification_question(axe_courant["nom"])
        elif should_force_simple_reformulation:
            state["question_courante"] = build_simple_reformulation_question(axe_courant["nom"])
        else:
            question = chain.invoke(payload)
            question = clean_question(question)
            state["question_courante"] = question or f"Pouvez-vous detailler votre experience en {axe_courant['nom']} ?"
    except Exception as exc:
        print(f"Erreur OpenRouter pendant la generation: {exc}")
        fallback_mode = question_mode
        if fallback_mode == "clarification":
            state["question_courante"] = build_simple_clarification_question(axe_courant["nom"])
        elif fallback_mode == "reformulation":
            state["question_courante"] = build_simple_reformulation_question(axe_courant["nom"])
        elif fallback_mode == "verification_incoherence":
            state["question_courante"] = f"Je vois une possible incoherence sur {axe_courant['nom']}. Pouvez-vous preciser ce point ?"
        else:
            state["question_courante"] = f"Pouvez-vous approfondir davantage votre reponse sur {axe_courant['nom']} ?"

    state["derniere_action"] = question_mode if question_mode != "question initiale" else "question"
    print(f"Question generee : {state['question_courante'][:100]}")
    return state
