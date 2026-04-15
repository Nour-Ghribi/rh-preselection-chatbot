# rh-preselection-chatbot

Chatbot RH de preselection base sur LangGraph, LangChain et OpenRouter.

## Fonctionnalites

- orchestration d'entretien avec LangGraph
- questions dynamiques selon CV + poste
- analyse structuree des reponses candidat
- logique metier Python pour clarification, approfondissement et scoring
- API FastAPI pour integration collaborative

## Lancer l'API

```powershell
pip install -r requirements.txt
uvicorn api:app --reload
```

Documentation interactive:

```text
http://127.0.0.1:8000/docs
```

## Endpoints principaux

- `POST /interview/start`
- `POST /interview/{session_id}/answer`
- `GET /interview/{session_id}`

## Configuration

Copier `.env.example` vers `.env` puis renseigner `OPENROUTER_API_KEY`.
