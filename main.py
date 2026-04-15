"""
Point d'entree principal du chatbot RH.

Charge les donnees, les valide, cree le graphe LangGraph,
l'execute et sauvegarde les resultats.
"""

import json
import os

from pydantic import ValidationError

from config.openrouter_config import validate_config, INTERVIEW_CONFIG
from models.interview_state import create_initial_state
from models.llm_schemas import CandidateInputModel, JobRequirementModel
from graph.langgraph_builder import build_interview_graph


def load_json_file(filepath: str) -> dict:
    """Charge un fichier JSON."""
    with open(filepath, "r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def validate_inputs(candidate_data: dict, job_data: dict):
    """Valide les JSON d'entree avec Pydantic."""
    try:
        candidate = CandidateInputModel.model_validate(candidate_data)
        job = JobRequirementModel.model_validate(job_data)
        return candidate.model_dump(), job.model_dump()
    except ValidationError as exc:
        raise ValueError(f"Validation JSON echouee:\n{exc}") from exc


def resolve_initial_score(candidate_data: dict, default_score: float = 0.78) -> float:
    """Retourne un score initial numerique meme si le champ est absent ou null."""
    raw_score = candidate_data.get("score_matching_init", default_score)
    if raw_score is None:
        return default_score
    try:
        return float(raw_score)
    except (TypeError, ValueError):
        return default_score


def save_json_file(filepath: str, data: dict):
    """Sauvegarde un dictionnaire en JSON."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as file_obj:
        json.dump(data, file_obj, indent=2, ensure_ascii=False)
    print(f"Resultat sauvegarde : {filepath}")


def format_final_result(final_state: dict) -> dict:
    """Formate l'etat final pour la sortie JSON."""
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


def main():
    """Fonction principale: orchestration complete du chatbot."""
    print("\n" + "=" * 70)
    print("CHATBOT RH - SYSTEME DE PRESELECTION AUTOMATIQUE")
    print("=" * 70)

    try:
        validate_config()

        candidate_file = "data/candidate_input.json"
        job_file = "data/job_requirement.json"

        print("\nChargement des donnees...")
        if not os.path.exists(candidate_file):
            raise FileNotFoundError(f"Fichier non trouve : {candidate_file}")
        if not os.path.exists(job_file):
            raise FileNotFoundError(f"Fichier non trouve : {job_file}")

        cv_candidat_raw = load_json_file(candidate_file)
        exigences_poste_raw = load_json_file(job_file)
        cv_candidat, exigences_poste = validate_inputs(cv_candidat_raw, exigences_poste_raw)

        score_matching_init = resolve_initial_score(cv_candidat, 0.78)

        print(f"Candidat : {cv_candidat.get('nom', 'N/A')}")
        print(f"Poste    : {exigences_poste.get('titre_poste', 'N/A')}")
        print(f"Score initial : {score_matching_init:.2f}")

        initial_state = create_initial_state(
            cv_candidat=cv_candidat,
            exigences_poste=exigences_poste,
            score_matching_init=score_matching_init,
        )

        print("\nConstruction du graphe LangGraph...")
        graph = build_interview_graph()

        print("\nExecution du chatbot d'entretien...")
        print("-" * 70)
        final_state = graph.invoke(
            initial_state,
            config={"recursion_limit": INTERVIEW_CONFIG["langgraph_recursion_limit"]},
        )

        result = format_final_result(final_state)
        candidate_name = cv_candidat.get("nom", "candidate").replace(" ", "_")
        output_file = f"output/interview_result_{candidate_name}.json"
        save_json_file(output_file, result)

        print("\n" + "=" * 70)
        print("ENTRETIEN TERMINE")
        print("=" * 70)
        print(f"Candidat         : {result['candidat']['nom']}")
        print(f"Poste            : {result['poste']['titre']}")
        print(
            f"Score            : {result['scoring']['score_matching_initial']:.2f} -> "
            f"{result['scoring']['score_final']:.2f}"
        )
        print(f"Recommandation   : {result['evaluation']['recommandation']}")
        print(f"Questions posees : {result['entretien']['nombre_questions']}")
        print(f"Fichier resultat : {output_file}")
        print("=" * 70 + "\n")
        return result
    except Exception as exc:
        print(f"\nERREUR : {exc}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
