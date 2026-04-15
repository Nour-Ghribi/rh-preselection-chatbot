"""
Noeud 3 : PRESENTATION_CANDIDAT

Responsabilites:
- Afficher la question au candidat (interface CLI)
- Attendre et collecter la reponse
- Supporter une saisie multi-ligne simple
- Stocker l'echange (Q/R) dans historique_qa
"""

from datetime import datetime

from models.interview_state import InterviewState


def collect_multiline_response() -> str:
    """
    Collecte une reponse CLI.

    Usage:
    - une seule ligne suffit si tu tapes directement la reponse puis Entree
    - si tu veux plusieurs lignes, colle-les puis termine avec une ligne contenant seulement FIN
    """
    print("Votre reponse:")
    print("  - reponse courte: tapez une ligne puis Entree")
    print("  - reponse longue: tapez/collez plusieurs lignes puis terminez par FIN")

    first_line = input("> ").rstrip()
    if first_line.strip() and first_line.strip().upper() != "FIN":
        return first_line.strip()

    lines = []
    if first_line.strip() and first_line.strip().upper() == "FIN":
        return ""

    while True:
        line = input()
        if line.strip().upper() == "FIN":
            break
        lines.append(line.rstrip())

    return "\n".join(lines).strip()


def presentation_candidate_node(state: InterviewState) -> InterviewState:
    """Interface CLI temporaire avec le candidat."""
    print("\n" + "=" * 60)
    print(f"Question {state['compteur_questions'] + 1}")
    print("=" * 60)
    print(f"\n{state['question_courante']}\n")

    reponse = ""
    while not reponse.strip():
        reponse = collect_multiline_response()
        if not reponse.strip():
            print("Veuillez fournir une reponse non vide.")

    axe_courant = state.get("axe_courant", {})
    nom_axe = axe_courant.get("nom")

    nouvel_echange = {
        "question": state["question_courante"],
        "reponse": reponse,
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

    print("Reponse enregistree.")
    return state
