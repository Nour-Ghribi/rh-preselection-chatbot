"""
Schemas de sorties LLM et de validation JSON.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResponseAnalysisOutput(BaseModel):
    nature_reponse: str = Field(description="suffisante, vague, partielle, hors_sujet, contradictoire, absence_competence, vide, refus, incomprehensible ou mixte_exploitable")
    qualite_reponse: str = Field(description="Excellente, Bonne, Moyenne, Faible ou Indeterminee")
    signal_metier: str = Field(description="positif, reserve, negatif ou critique")
    confiance: float = Field(description="Score de confiance entre 0.0 et 1.0")
    besoin_relance: bool = Field(description="True si une relance sur le meme axe est necessaire")
    type_relance: str = Field(description="clarification, approfondissement, reformulation, verification_incoherence ou aucune")
    coherence_cv: str = Field(description="coherent, contradictoire ou non_verifiable")
    couverture_axe: str = Field(description="complete, partielle ou insuffisante")
    evidence_level: str = Field(description="explicite, implicite ou absent")
    alignment_question: str = Field(description="direct, partiel ou indirect")
    justification_courte: str = Field(description="Justification courte de l'analyse")


class FinalEvaluationOutput(BaseModel):
    score_final: float = Field(description="Score final entre 0.0 et 1.0")
    points_forts: List[str] = Field(description="Liste des principaux points forts")
    points_faibles: List[str] = Field(description="Liste des principaux points faibles")
    zones_de_doute: List[str] = Field(description="Liste des points a clarifier")
    recommandation: str = Field(description="A convoquer, A rejeter ou Dossier a examiner manuellement")
    resume: str = Field(description="Resume global de l'entretien")


class ExperienceItem(BaseModel):
    titre: str
    entreprise: Optional[str] = None
    description: Optional[str] = None
    duree_mois: Optional[int] = None


class CandidateInputModel(BaseModel):
    nom: str
    email: Optional[str] = None
    telephone: Optional[str] = None
    competences: Dict[str, List[str]]
    experiences: List[ExperienceItem] = []
    projets_personnels: List[Dict[str, Any]] = []
    langues: List[str] = []
    disponibilite: Optional[str] = None
    pretention_salariale: Optional[str] = None
    score_matching_init: Optional[float] = None


class JobRequirementModel(BaseModel):
    titre_poste: str
    entreprise: Optional[str] = None
    competences_obligatoires: List[str]
    competences_tres_appreciees: List[str] = []
    soft_skills_requis: List[str] = []
    experience_requise: Dict[str, Any] = {}
    conditions: Dict[str, Any] = {}
