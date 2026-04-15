API Usage

Lancer l'API:

```powershell
uvicorn api:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Endpoints principaux:

1. `POST /interview/start`

Body:

```json
{
  "cv": {
    "nom": "Aymen Ben Ali",
    "competences": {
      "langages": ["Python", "SQL"]
    },
    "experiences": []
  },
  "job": {
    "titre_poste": "Data Scientist",
    "competences_obligatoires": ["Python avancé", "Machine Learning"]
  },
  "score_matching_initial": 0.78
}
```

Reponse:

```json
{
  "session_id": "uuid",
  "status": "in_progress",
  "question": "Pouvez-vous ...",
  "summary": {
    "current_axis": "Python avancé",
    "question_count": 0,
    "covered_axes": 0,
    "total_axes": 8,
    "score_entretien": 0.0
  }
}
```

2. `POST /interview/{session_id}/answer`

Body:

```json
{
  "answer": "J'ai utilisé Python dans plusieurs projets..."
}
```

Si l'entretien continue:

```json
{
  "session_id": "uuid",
  "status": "in_progress",
  "question": "Question suivante ...",
  "summary": {
    "current_axis": "Machine Learning",
    "question_count": 1,
    "covered_axes": 1,
    "total_axes": 8,
    "score_entretien": 0.06
  }
}
```

Si l'entretien est termine:

```json
{
  "session_id": "uuid",
  "status": "completed",
  "result": {
    "candidat": {},
    "poste": {},
    "scoring": {},
    "evaluation": {},
    "entretien": {}
  },
  "summary": {
    "current_axis": null,
    "question_count": 6,
    "covered_axes": 6,
    "total_axes": 8,
    "score_entretien": 0.12
  }
}
```

3. `GET /interview/{session_id}`

Permet de recuperer l'etat courant ou le resultat final.
