"""
Noeud 1 : INITIALIZATION_CONTEXTE

Responsabilites:
- Valider les JSON d'entree
- Extraire les axes a tester
- Prioriser les axes et leur importance
- Initialiser l'etat pour la boucle d'entretien
"""

import unicodedata
from typing import Dict, Any, List

from models.interview_state import InterviewState


def normalize_text(value: str) -> str:
    """Normalise un texte pour les comparaisons simples."""
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    cleaned = []
    for char in ascii_text.lower():
        cleaned.append(char if char.isalnum() or char.isspace() else " ")
    return " ".join("".join(cleaned).split())


def split_requirement_terms(requirement: str) -> List[str]:
    """Decoupe une exigence en sous-termes simples."""
    normalized = normalize_text(requirement)
    separators = ["(", ")", ",", "/", " et "]
    terms = [normalized]
    for sep in separators:
        expanded = []
        for term in terms:
            expanded.extend([part.strip() for part in term.split(sep) if part.strip()])
        terms = expanded
    return [term for term in terms if len(term) >= 3]


def requirement_matches_cv(requirement: str, cv_skills: List[str]) -> bool:
    """Teste si une exigence correspond au moins partiellement au CV."""
    requirement_terms = split_requirement_terms(requirement)
    if not requirement_terms:
        return False

    for term in requirement_terms:
        for skill in cv_skills:
            if term in skill or skill in term:
                return True
    return False


def make_axis(
    axis_id: str,
    name: str,
    priorite: int,
    axis_type: str,
    importance_axe: str,
    status: str,
    critique: bool,
) -> Dict[str, Any]:
    """Construit un axe normalise."""
    return {
        "id": axis_id,
        "nom": name,
        "priorite": priorite,
        "type": axis_type,
        "importance": importance_axe,
        "importance_axe": importance_axe,
        "status": status,
        "critique": critique,
    }


def extraire_axes_automatiquement(cv_candidat: Dict[str, Any], exigences_poste: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrait les axes a tester par logique deterministe."""
    axes: List[Dict[str, Any]] = []
    priorite_counter = 1

    competences_obligatoires = exigences_poste.get("competences_obligatoires", [])
    competences_cv = cv_candidat.get("competences", {})

    cv_skills_flat: List[str] = []
    for _, skills in competences_cv.items():
        if isinstance(skills, list):
            cv_skills_flat.extend(normalize_text(str(skill)) for skill in skills)

    for idx, comp_oblig in enumerate(competences_obligatoires, start=1):
        is_in_cv = requirement_matches_cv(comp_oblig, cv_skills_flat)
        axes.append(
            make_axis(
                axis_id=f"critique_{idx}",
                name=comp_oblig,
                priorite=priorite_counter,
                axis_type="competence_confirmable" if is_in_cv else "competence_gap",
                importance_axe="critique",
                status="declare_dans_cv" if is_in_cv else "absent_du_cv",
                critique=True,
            )
        )
        priorite_counter += 1

    competences_appreciees = exigences_poste.get("competences_tres_appreciees", [])[:2]
    for idx, comp_app in enumerate(competences_appreciees, start=1):
        if requirement_matches_cv(comp_app, cv_skills_flat):
            continue
        axes.append(
            make_axis(
                axis_id=f"important_{idx}",
                name=comp_app,
                priorite=priorite_counter,
                axis_type="competence_gap",
                importance_axe="important",
                status="absent_du_cv",
                critique=False,
            )
        )
        priorite_counter += 1

    for idx, soft_skill in enumerate(exigences_poste.get("soft_skills_requis", [])[:2], start=1):
        axes.append(
            make_axis(
                axis_id=f"soft_{idx}",
                name=soft_skill,
                priorite=priorite_counter,
                axis_type="soft_skill",
                importance_axe="secondaire",
                status="a_evaluer",
                critique=False,
            )
        )
        priorite_counter += 1

    experiences = cv_candidat.get("experiences", [])
    if experiences:
        exp_recente = experiences[0]
        axes.append(
            make_axis(
                axis_id="experience_principale",
                name=f"Experience {exp_recente.get('titre', 'professionnelle')}",
                priorite=priorite_counter,
                axis_type="experience_cle",
                importance_axe="important",
                status="a_approfondir",
                critique=False,
            )
        )
        priorite_counter += 1

    axes.append(
        make_axis(
            axis_id="motivation_poste",
            name="Motivation pour le poste",
            priorite=priorite_counter,
            axis_type="motivation",
            importance_axe="secondaire",
            status="a_evaluer",
            critique=False,
        )
    )

    axes.sort(key=lambda item: item["priorite"])
    return axes


def initialization_node(state: InterviewState) -> InterviewState:
    """Initialise le contexte de l'entretien."""
    print("\n" + "=" * 60)
    print("INITIALISATION DE L'ENTRETIEN")
    print("=" * 60)

    if not state["cv_candidat"]:
        raise ValueError("CV candidat vide")
    if not state["exigences_poste"]:
        raise ValueError("Exigences du poste vides")

    print(f"Candidat : {state['cv_candidat'].get('nom', 'Anonyme')}")
    print(f"Poste    : {state['exigences_poste'].get('titre_poste', 'Inconnu')}")
    print(f"Score initial : {state['score_matching_init']:.2f}")

    axes = extraire_axes_automatiquement(state["cv_candidat"], state["exigences_poste"])

    state["axes_a_tester"] = axes
    state["axes_couverts"] = []
    state["validated_axes"] = []
    state["weak_axes"] = []
    state["critical_failures"] = []
    state["inconsistencies"] = []
    state["historique_qa"] = []
    state["decision_trace"] = []
    state["axe_courant"] = {}
    state["relances_par_axe"] = {}
    state["axis_attempts"] = {
        axe["nom"]: {
            "clarification": 0,
            "approfondissement": 0,
            "reformulation": 0,
            "verification_incoherence": 0,
        }
        for axe in axes
    }
    state["question_courante"] = ""
    state["compteur_questions"] = 0
    state["score_entretien"] = 0.0
    state["signal_arret"] = False
    state["raison_arret"] = ""
    state["derniere_action"] = "question"

    print(f"\nPlan d'entretien ({len(axes)} axes) :")
    for index, axe in enumerate(axes, 1):
        print(
            f"  {index}. {axe['nom']} | type={axe['type']} | importance={axe['importance_axe']} | "
            f"priorite={axe['priorite']} | status={axe['status']}"
        )

    print("\nContexte initialise. Pret a generer la premiere question.\n")
    return state
