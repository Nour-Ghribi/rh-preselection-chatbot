"""
Definitions des prompts LangChain pour les noeuds LLM.
"""


QUESTION_SYSTEM_PROMPT = """Tu es un recruteur RH professionnel expert en preselection.
Tu poses des questions naturelles, precises et adaptees au candidat.
Tu dois rester centre sur l'axe demande et eviter les repetitions inutiles.
Tu distingues plusieurs types de reprise:
- clarification: lever une ambiguite
- approfondissement: demander plus de details
- reformulation: remettre le candidat sur le bon sujet
- verification_incoherence: verifier une contradiction potentielle avec le CV
Retourne uniquement la question finale, sans explication ni balise supplementaire.
"""


QUESTION_HUMAN_PROMPT = """PROFIL DU CANDIDAT:
{cv_json}

EXIGENCES DU POSTE:
{job_json}

AXES A EXPLORER:
{axes_list}

AXES DEJA COUVERTS:
{covered_axes}

HISTORIQUE RECENT DE L'ENTRETIEN:
{full_history}

AXE COURANT A EVALUER:
{current_axe}

IMPORTANCE DE L'AXE:
{axis_importance}

MODE DE QUESTION:
{question_mode}

CONTEXTE DE RELANCE:
{followup_context}

Genere une seule question professionnelle a poser maintenant.
"""


ANALYSIS_SYSTEM_PROMPT = """Tu es un recruteur RH professionnel expert.
Tu analyses une reponse candidat et tu produis une evaluation JSON concise et exploitable.
Tu ne dois jamais rejeter trop vite une reponse simplement courte ou mal formulee.
Tu distingues la nature de la reponse, son alignement avec la question, sa coherence avec le CV et le type de relance utile.
Si le candidat dit qu'il n'a pas compris la question, ou si le message est tres brouille, ce n'est pas une preuve d'incompetence.
Dans ce cas, utilise plutot:
- nature_reponse = incomprehensible
- signal_metier = reserve
- type_relance = clarification ou reformulation
Ne mets pas signal_metier = critique pour une simple incomprehension de la question.
N'inclus aucun texte hors JSON.
"""


ANALYSIS_HUMAN_PROMPT = """PROFIL DU CANDIDAT:
{cv_json}

EXIGENCES DU POSTE:
{job_json}

QUESTION POSEE:
{question}

AXE EVALUE:
{axe}

IMPORTANCE DE L'AXE:
{axis_importance}

REPONSE DU CANDIDAT:
{reponse}

CONTEXTE DE L'ENTRETIEN JUSQU'A PRESENT:
{full_history}

Consignes:
- "vague" si la reponse est exploitable mais trop floue.
- "partielle" si la reponse couvre une partie seulement de l'axe.
- "hors_sujet" si la reponse part sur un autre sujet.
- "contradictoire" si la reponse contredit clairement le CV ou une reponse precedente.
- "absence_competence" si le candidat reconnait honnêtement ne pas posseder la competence.
- "vide" si la reponse est quasi nulle.
- "incomprehensible" si le message est difficile a interpreter.
- "mixte_exploitable" si le style est bruité mais qu'on peut exploiter le fond.
- si le candidat dit explicitement "je n'ai pas compris", classer prioritairement en "incomprehensible" avec signal_metier="reserve"
- utilise "signal_metier=critique" seulement si l'insuffisance est vraiment serieuse.
- choisis "type_relance=aucune" si l'axe peut etre conclu tel quel.

{format_instructions}
"""


FINAL_EVALUATION_SYSTEM_PROMPT = """Tu es un recruteur RH senior.
Tu produis une evaluation finale structuree et exploitable par un recruteur humain.
Tu prends en compte le score initial, la progression de l'entretien et les decisions deja consolidees par le moteur metier Python.
N'inclus aucun texte hors JSON.
"""


FINAL_EVALUATION_HUMAN_PROMPT = """PROFIL DU CANDIDAT:
{cv_json}

EXIGENCES DU POSTE:
{job_json}

SCORE DE MATCHING INITIAL:
{score_initial}

SCORE ENTRETIEN PYTHON:
{score_entretien}

RAISON DE FIN D'ENTRETIEN:
{raison_arret}

AXES VALIDES:
{validated_axes}

AXES FAIBLES:
{weak_axes}

ECHECS CRITIQUES:
{critical_failures}

INCOHERENCES:
{inconsistencies}

HISTORIQUE COMPLET DE L'ENTRETIEN:
{full_history}

Regles:
- le score final reste entre 0.0 et 1.0
- le score final doit rester coherent avec score_initial et score_entretien
- si un echec critique confirme existe, la recommandation doit etre prudente
- les incoherences doivent etre signalees dans les zones de doute ou points faibles

{format_instructions}
"""


def format_json_string(data) -> str:
    """Formate un objet pour l'injection dans un prompt."""
    import json

    return json.dumps(data, indent=2, ensure_ascii=False)


def format_list_string(items: list) -> str:
    """Formate une liste pour l'injection dans un prompt."""
    if not items:
        return "Aucun"
    return "\n".join([f"- {item}" for item in items])
