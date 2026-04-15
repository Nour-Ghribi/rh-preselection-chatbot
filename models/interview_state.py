"""
Etat partage LangGraph pour l'entretien de preselection.
Chaque noeud lit et met a jour cet etat.
"""

from typing import TypedDict, List, Dict, Any


class InterviewState(TypedDict):
    """
    Etat central qui circule entre tous les noeuds du graphe LangGraph.
    Tous les champs doivent etre serialisables en JSON.
    """

    cv_candidat: Dict[str, Any]
    exigences_poste: Dict[str, Any]
    score_matching_init: float

    axes_a_tester: List[Dict[str, Any]]
    axes_couverts: List[str]
    validated_axes: List[str]
    weak_axes: List[Dict[str, Any]]
    critical_failures: List[Dict[str, Any]]
    inconsistencies: List[Dict[str, Any]]

    historique_qa: List[Dict[str, Any]]
    decision_trace: List[Dict[str, Any]]

    axe_courant: Dict[str, Any]
    question_courante: str
    compteur_questions: int
    relances_par_axe: Dict[str, int]
    axis_attempts: Dict[str, Dict[str, int]]

    score_entretien: float
    signal_arret: bool
    raison_arret: str
    derniere_action: str

    score_final: float
    resume_entretien: str
    points_forts: List[str]
    points_faibles: List[str]
    zones_de_doute: List[str]
    recommandation: str


def create_initial_state(
    cv_candidat: Dict[str, Any],
    exigences_poste: Dict[str, Any],
    score_matching_init: float = 0.5,
) -> InterviewState:
    """Cree l'etat initial pour demarrer un entretien."""
    return InterviewState(
        cv_candidat=cv_candidat,
        exigences_poste=exigences_poste,
        score_matching_init=score_matching_init,
        axes_a_tester=[],
        axes_couverts=[],
        validated_axes=[],
        weak_axes=[],
        critical_failures=[],
        inconsistencies=[],
        historique_qa=[],
        decision_trace=[],
        axe_courant={},
        question_courante="",
        compteur_questions=0,
        relances_par_axe={},
        axis_attempts={},
        score_entretien=0.0,
        signal_arret=False,
        raison_arret="",
        derniere_action="question",
        score_final=0.0,
        resume_entretien="",
        points_forts=[],
        points_faibles=[],
        zones_de_doute=[],
        recommandation="",
    )
