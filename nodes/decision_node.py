"""
Noeud 5 : DECISION_SUITE

Responsabilites:
- Evaluer les conditions d'arret
- Decider: continuer, relancer typiquement, ou terminer
- Consolider un scoring hybride controle cote Python
"""

from typing import Dict, Any

from models.interview_state import InterviewState
from config.openrouter_config import INTERVIEW_CONFIG


RELANCE_BY_NATURE = {
    "vague": "clarification",
    "partielle": "approfondissement",
    "hors_sujet": "reformulation",
    "contradictoire": "verification_incoherence",
    "incomprehensible": "reformulation",
    "vide": "clarification",
}

SCORE_MULTIPLIER_BY_QUALITY = {
    "Excellente": 1.0,
    "Bonne": 0.7,
    "Moyenne": 0.3,
    "Faible": -0.7,
    "Indeterminee": -0.2,
}

NATURE_SCORE_FACTOR = {
    "suffisante": 1.0,
    "vague": -0.2,
    "partielle": -0.1,
    "hors_sujet": -0.3,
    "contradictoire": -0.8,
    "absence_competence": -1.0,
    "vide": -0.4,
    "refus": -0.6,
    "incomprehensible": -0.4,
    "mixte_exploitable": 0.0,
}


def is_critical_axis(axis: Dict[str, Any]) -> bool:
    """Determine si un axe peut porter une decision plus severe."""
    return axis.get("importance_axe") == "critique" or bool(axis.get("critique"))


def add_decision_trace(state: InterviewState, axis_name: str, action: str, reason: str):
    """Ajoute une trace lisible de la decision prise."""
    state["decision_trace"].append(
        {
            "axe": axis_name,
            "action": action,
            "reason": reason,
            "question_index": state["compteur_questions"],
        }
    )


def mark_axis_as_covered(state: InterviewState, axis_name: str):
    """Marque proprement un axe comme couvert."""
    if axis_name and axis_name not in state["axes_couverts"]:
        state["axes_couverts"].append(axis_name)


def add_unique_fact(bucket: list, item: Dict[str, Any], key: str = "axe"):
    """Ajoute un element dans une liste si l'axe n'y figure pas deja."""
    axe = item.get(key)
    if axe and all(existing.get(key) != axe for existing in bucket):
        bucket.append(item)


def get_axis_weight(axis: Dict[str, Any]) -> float:
    """Retourne le poids de scoring d'un axe selon son importance."""
    weights = INTERVIEW_CONFIG["score_weights"]
    return weights.get(axis.get("importance_axe", "important"), weights["important"])


def update_interview_score(state: InterviewState, axis: Dict[str, Any], analyse: Dict[str, Any]):
    """Calcule un ajustement progressif de score d'entretien."""
    quality = analyse.get("qualite_reponse", "Indeterminee")
    nature = analyse.get("nature_reponse", "partielle")
    confidence = float(analyse.get("confiance", 0.0))
    weight = get_axis_weight(axis)
    delta = weight * (SCORE_MULTIPLIER_BY_QUALITY.get(quality, -0.2) + NATURE_SCORE_FACTOR.get(nature, 0.0))
    delta *= max(0.35, confidence)
    state["score_entretien"] = round(state["score_entretien"] + delta, 4)


def build_failure_payload(axis_name: str, analyse: Dict[str, Any]) -> Dict[str, Any]:
    """Construit un resume d'echec ou de faiblesse."""
    return {
        "axe": axis_name,
        "nature_reponse": analyse.get("nature_reponse"),
        "signal_metier": analyse.get("signal_metier"),
        "confiance": analyse.get("confiance"),
        "justification": analyse.get("justification_courte"),
    }


def relance_allowed(state: InterviewState, axis_name: str, relance_type: str) -> bool:
    """Verifie si une relance du type demande est encore autorisee."""
    axis_attempts = state["axis_attempts"].get(axis_name, {})
    return axis_attempts.get(relance_type, 0) < 1


def is_explicit_question_not_clear(answer_text: str) -> bool:
    """Detecte les formulations explicites du type 'je n'ai pas compris la question'."""
    normalized = (answer_text or "").lower()
    markers = [
        "je ne comprend",
        "je n ai pas compris",
        "j ai pas compris",
        "pas compris la question",
        "question pas claire",
        "je ne comprends pas",
    ]
    return any(marker in normalized for marker in markers)


def finalize_axis(state: InterviewState, axis: Dict[str, Any], analyse: Dict[str, Any]):
    """Cloture proprement un axe suivant l'analyse obtenue."""
    axis_name = axis.get("nom")
    nature = analyse.get("nature_reponse", "partielle")
    coherence_cv = analyse.get("coherence_cv", "non_verifiable")

    mark_axis_as_covered(state, axis_name)

    if analyse.get("couverture_axe") == "complete" and nature in {"suffisante", "mixte_exploitable"}:
        if axis_name not in state["validated_axes"]:
            state["validated_axes"].append(axis_name)
        add_decision_trace(state, axis_name, "valider_axe", "Axe couvert et reponse satisfaisante.")
    else:
        add_unique_fact(state["weak_axes"], build_failure_payload(axis_name, analyse))
        add_decision_trace(state, axis_name, "cloture_axe_faible", "Axe traite mais non completement valide.")

    if coherence_cv == "contradictoire" or nature == "contradictoire":
        add_unique_fact(state["inconsistencies"], build_failure_payload(axis_name, analyse))

    if is_critical_axis(axis) and nature in {"absence_competence", "contradictoire"}:
        add_unique_fact(state["critical_failures"], build_failure_payload(axis_name, analyse))

    state["axe_courant"] = {}


def should_stop_immediately(axis: Dict[str, Any], analyse: Dict[str, Any], relance_possible: bool) -> bool:
    """Determine si un arret immediat est justifie."""
    if not is_critical_axis(axis):
        return False
    if analyse.get("signal_metier") != "critique":
        return False
    if analyse.get("confiance", 0.0) < INTERVIEW_CONFIG["critical_stop_confidence_threshold"]:
        return False
    if analyse.get("besoin_relance", False) or relance_possible:
        return False
    if analyse.get("nature_reponse") not in {"absence_competence", "contradictoire"}:
        return False
    return True


def decision_node(state: InterviewState) -> InterviewState:
    """Decide si l'entretien continue ou s'arrete."""
    print("\n" + "=" * 60)
    print("DECISION : continuer ou arreter")
    print("=" * 60)

    if not state["historique_qa"]:
        state["signal_arret"] = True
        state["raison_arret"] = "entretien_vide"
        state["derniere_action"] = "fin"
        return state

    if state["compteur_questions"] >= INTERVIEW_CONFIG["max_questions"]:
        state["signal_arret"] = True
        state["raison_arret"] = "max_questions"
        state["derniere_action"] = "fin"
        print(f"Limite globale de questions atteinte ({state['compteur_questions']}/{INTERVIEW_CONFIG['max_questions']}).")
        return state

    derniere_qa = state["historique_qa"][-1]
    analyse = derniere_qa.get("analyse", {})
    axe_courant = state.get("axe_courant") or {}
    nom_axe = axe_courant.get("nom", derniere_qa.get("axe"))
    if not axe_courant:
        axe_courant = next((axe for axe in state["axes_a_tester"] if axe["nom"] == nom_axe), {})

    nature = analyse.get("nature_reponse", "partielle")
    couverture_axe = analyse.get("couverture_axe", "partielle")
    requested_relance = analyse.get("type_relance", "aucune")
    explicit_not_clear = is_explicit_question_not_clear(derniere_qa.get("reponse", ""))
    if requested_relance == "aucune" and nature in RELANCE_BY_NATURE:
        requested_relance = RELANCE_BY_NATURE[nature]

    if explicit_not_clear and state.get("derniere_action") == "clarification":
        requested_relance = "reformulation"

    relance_possible = requested_relance != "aucune" and relance_allowed(state, nom_axe, requested_relance)
    update_interview_score(state, axe_courant, analyse)

    if should_stop_immediately(axe_courant, analyse, relance_possible):
        payload = build_failure_payload(nom_axe, analyse)
        add_unique_fact(state["critical_failures"], payload)
        add_decision_trace(state, nom_axe, "arret_immediat", "Echec critique confirme sans relance utile.")
        state["signal_arret"] = True
        state["raison_arret"] = "signal_critique_confirme"
        state["derniere_action"] = "fin"
        print(f"Arret immediat confirme sur axe critique: {nom_axe}")
        return state

    if nature == "refus":
        add_unique_fact(state["weak_axes"], build_failure_payload(nom_axe, analyse))
        add_decision_trace(state, nom_axe, "penalite_refus", "Refus de repondre sur cet axe.")

    if relance_possible:
        state["signal_arret"] = False
        state["raison_arret"] = ""
        state["derniere_action"] = requested_relance
        add_decision_trace(state, nom_axe, requested_relance, analyse.get("justification_courte", "Relance utile."))
        print(f"Relance {requested_relance} sur l'axe {nom_axe}.")
        return state

    if nature in {"vague", "partielle", "vide", "incomprehensible", "hors_sujet"} and couverture_axe != "complete":
        add_unique_fact(state["weak_axes"], build_failure_payload(nom_axe, analyse))
        add_decision_trace(
            state,
            nom_axe,
            "cloture_sous_reserve",
            "Axe cloture faute de relance utile restante, mais reponse encore insuffisante.",
        )

    finalize_axis(state, axe_courant, analyse)

    if len(state["axes_couverts"]) >= len(state["axes_a_tester"]):
        state["signal_arret"] = True
        state["raison_arret"] = "axes_couverts"
        state["derniere_action"] = "fin"
        print("Tous les axes prioritaires ont ete couverts.")
        return state

    if len(state["critical_failures"]) >= 2:
        state["signal_arret"] = True
        state["raison_arret"] = "plusieurs_echecs_critiques"
        state["derniere_action"] = "fin"
        print("Arret apres accumulation d'echecs critiques confirmes.")
        return state

    state["signal_arret"] = False
    state["raison_arret"] = ""
    state["derniere_action"] = "question"
    print(
        f"On continue. Axes couverts : {len(state['axes_couverts'])}/{len(state['axes_a_tester'])} | "
        f"Questions : {state['compteur_questions']}/{INTERVIEW_CONFIG['max_questions']} | "
        f"Score entretien: {state['score_entretien']:.3f}"
    )
    return state
