"""
Script de validation du projet.
Verifie que les imports fonctionnent et que la structure est correcte.
"""

import os
import sys


def check_file_exists(filepath: str, description: str) -> bool:
    """Verifie qu'un fichier existe."""
    if os.path.exists(filepath):
        print(f"[OK] {description}")
        return True
    print(f"[KO] {description} - MANQUANT")
    return False


def check_imports() -> bool:
    """Verifie les dependances Python importantes."""
    print("\nVerification des imports Python...")

    modules = [
        ("langgraph", "pip install langgraph"),
        ("langchain", "pip install langchain"),
        ("langchain_openai", "pip install langchain-openai"),
        ("pydantic", "pip install pydantic"),
    ]

    all_ok = True
    for module_name, install_hint in modules:
        try:
            __import__(module_name)
            print(f"  [OK] {module_name}")
        except ImportError:
            print(f"  [KO] {module_name} ({install_hint})")
            all_ok = False

    return all_ok


def check_structure() -> bool:
    """Verifie la structure du projet."""
    print("\nVerification de la structure...")
    checks = [
        ("config/openrouter_config.py", "Configuration OpenRouter"),
        ("config/prompts.py", "Templates de prompts"),
        ("models/interview_state.py", "Etat du graphe"),
        ("nodes/initialization.py", "Noeud 1 - Initialisation"),
        ("nodes/question_generation.py", "Noeud 2 - Generation question"),
        ("nodes/candidate_presentation.py", "Noeud 3 - Presentation candidat"),
        ("nodes/response_analysis.py", "Noeud 4 - Analyse reponse"),
        ("nodes/decision_node.py", "Noeud 5 - Decision"),
        ("nodes/final_evaluation.py", "Noeud 6 - Evaluation finale"),
        ("graph/langgraph_builder.py", "Builder du graphe"),
        ("data/candidate_input.json", "Donnees test - Candidat"),
        ("data/job_requirement.json", "Donnees test - Poste"),
        ("main.py", "Point d'entree"),
        ("requirements.txt", "Dependances"),
        ("START_HERE.md", "Documentation de depart"),
    ]

    all_ok = True
    for filepath, desc in checks:
        full_path = os.path.join(os.getcwd(), filepath)
        if not check_file_exists(full_path, desc):
            all_ok = False
    return all_ok


def check_env_config() -> bool:
    """Verifie la configuration .env."""
    print("\nVerification de la configuration...")
    if not os.path.exists(".env"):
        print("[KO] Fichier .env manquant")
        return False

    with open(".env", "r", encoding="utf-8") as file_obj:
        env_content = file_obj.read()

    if "OPENROUTER_API_KEY" in env_content:
        print("[OK] .env present avec OPENROUTER_API_KEY")
        return True

    print("[KO] OPENROUTER_API_KEY absente du .env")
    return False


def check_project_imports() -> bool:
    """Teste les imports internes du projet."""
    print("\nVerification des imports du projet...")
    try:
        from models.interview_state import InterviewState, create_initial_state  # noqa: F401
        from config.openrouter_config import create_llm_client  # noqa: F401
        from nodes.initialization import initialization_node  # noqa: F401
        from nodes.question_generation import generation_question_node  # noqa: F401
        from nodes.candidate_presentation import presentation_candidate_node  # noqa: F401
        from nodes.response_analysis import response_analysis_node  # noqa: F401
        from nodes.decision_node import decision_node  # noqa: F401
        from nodes.final_evaluation import final_evaluation_node  # noqa: F401
        from graph.langgraph_builder import build_interview_graph  # noqa: F401
    except ImportError as exc:
        print(f"[KO] Import interne echoue: {exc}")
        return False

    print("[OK] Imports internes fonctionnels")
    return True


def main() -> int:
    """Execute toutes les verifications."""
    print("\n" + "=" * 60)
    print("VALIDATION DU PROJET - CHATBOT RH")
    print("=" * 60)

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    structure_ok = check_structure()
    imports_ok = check_imports()
    env_ok = check_env_config()
    project_imports_ok = check_project_imports()

    print("\n" + "=" * 60)
    print("RESUME")
    print("=" * 60)

    if structure_ok and imports_ok and env_ok and project_imports_ok:
        print("\n[OK] Tout est pret. Lance: python main.py\n")
        return 0

    print("\n[ATTENTION] Certains elements sont a corriger avant python main.py\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
