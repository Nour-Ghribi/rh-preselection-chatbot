# 🚀 GUIDE RAPIDE D'EXÉCUTION

## ✅ Le projet est COMPLÈTEMENT créé et fonctionnel!

Tous les fichiers Python, les nœuds LangGraph, les configurations et les données de test sont prêts.

---

## 📦 Installation d'une seule ligne

Copiez-collez cette commande dans PowerShell/Terminal:

```powershell
cd c:\Users\nourg\Desktop\nlpcvfinal && pip install -r requirements.txt && python main.py
```

---

## 🔑 Avant d'exécuter

### 1️⃣ Créer/Éditer `.env`

Ouvrir `c:\Users\nourg\Desktop\nlpcvfinal\.env` et remplacer par:

```env
OPENROUTER_API_KEY=sk_live_xxxxx
```

(Remplacer `sk_live_xxxxx` par votre vraie clé API OpenRouter)

### 2️⃣ Comment obtenir la clé API?

1. Aller sur https://openrouter.ai/sign-up
2. Créer un compte (ou se connecter)
3. Aller dans Settings → API Keys
4. Copier votre clé (commence par `sk_`)
5. Coller dans `.env`

---

## ▶️ Exécution

### Commande Simple (Recommandé)

```bash
cd c:\Users\nourg\Desktop\nlpcvfinal
python main.py
```

### Avec Environnement Virtuel (Optionnel)

```bash
cd c:\Users\nourg\Desktop\nlpcvfinal
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## 📋 Ce que vous verrez

```
======================================================
🎯 CHATBOT RH - SYSTÈME DE PRÉSÉLECTION AUTOMATIQUE
======================================================

📂 Chargement des données...
✅ Candidat: Aymen Ben Ali
✅ Poste: Data Scientist

🔧 INITIALISATION DE L'ENTRETIEN
📋 Plan d'entretien (5 axes à explorer):
   1. Python
   2. NLP
   3. Autonomie
   ...

❓ Question 1:
Pouvez-vous me parler d'un projet Python que vous avez mené?

📝 Votre réponse: [VOUS ÉCRIVEZ ICI]

[L'entretien continue avec 5-7 questions alternées...]

✅ ENTRETIEN TERMINÉ
📊 RÉSUMÉ FINAL:
   Score: 0.78 → 0.85
   Recommandation: À convoquer
   Fichier résultat: output/interview_result_Aymen_Ben_Ali.json
```

---

## 🎯 Structure Complète du Projet

```
nlpcvfinal/
├── 📄 main.py                    👈 LANCER CEL
├── 📝 README.md                  (Documentation complète)
├── 🔍 validate.py               (Validation du projet)
├── 📋 EXECUTION_SUMMARY.md      (Résumé technique)
├── 📁 config/
│   ├── openrouter_config.py     (Config API, modèle LLM)
│   └── prompts.py               (Templates de prompts)
├── 📁 models/
│   └── interview_state.py        (État du graphe)
├── 📁 nodes/                     (6 nœuds LangGraph)
│   ├── initialization.py
│   ├── question_generation.py
│   ├── candidate_presentation.py
│   ├── response_analysis.py
│   ├── decision_node.py
│   └── final_evaluation.py
├── 📁 graph/
│   └── langgraph_builder.py      (Construction graphe)
├── 📁 data/
│   ├── candidate_input.json      (Données test)
│   └── job_requirement.json      (Données test)
├── 📁 output/                    (Résultats générés)
├── 📁 .env                       👈 ÉDITER AVEC VOTRE CLÉ API
└── 📄 requirements.txt            (Dépendances pip)
```

---

## ❓ Personnalisation

### Modifier le candidat/poste

Éditer:
- `data/candidate_input.json` - Profil du candidat
- `data/job_requirement.json` - Exigences du poste

Relancer `main.py` et les données seront utilisées.

### Augmenter le nombre de questions

Éditer `config/openrouter_config.py`:
```python
INTERVIEW_CONFIG = {
    "max_questions": 10,  # Était 7
}
```

### Changer le modèle LLM

Éditer `config/openrouter_config.py`:
```python
LLM_MODEL = "openai/gpt-4"  # Au lieu de Llama
```

---

## 🐛 Si vous avez un problème

### "ModuleNotFoundError: No module named 'langgraph'"

Solution:
```bash
pip install langgraph langchain langchain-openai
```

### "OPENROUTER_API_KEY not defined"

Solution:
1. Ouvrir `.env`
2. Y ajouter: `OPENROUTER_API_KEY=sk_live_xxxxx`
3. Sauvegarder

### "FileNotFoundError: data/candidate_input.json"

Solution:
- Les fichiers JSON doivent être dans le dossier `data/`
- Vérifier que les fichiers n'ont pas été déplacés

### Connexion très lente

- Normal pour OpenRouter initialement (~10s par question)
- Les appels LLM prennent du temps
- Vous pouvez changer le modèle pour plus rapide

---

## 📊 Résultat

Après l'entretien, un fichier JSON est créé:
```
output/interview_result_Aymen_Ben_Ali.json
```

Contient:
- ✅ Score initial vs score final
- ✅ Points forts / faibles
- ✅ Recommandation (À convoquer / À rejeter / Dossier manuel)
- ✅ Historique complet des Q/R
- ✅ Analyse par axe

---

## ⭐ La Magie du Système

Chaque question est générée avec:
- ✅ Tout le contexte du candidat
- ✅ Les exigences du poste
- ✅ **TOUTES les réponses précédentes**
- ✅ Les axes déjà couverts

Résultat:
- **Pas de répétitions**
- **Questions cohérentes et progressives**
- **Adaptation réelle au candidat**

---

## 🎓 Architecture

### Stack Technique

- **Python** 3.11+
- **LangGraph** - Orchestration avec cycles
- **LangChain** - Construction des prompts
- **OpenRouter** - Accès aux LLM
- **Pydantic** - Validation des données

### Les 6 Nœuds LangGraph

1. INIT (parse données)
2. GEN_Q (LLM) → génère question
3. PRESENT → collecte réponse
4. ANALYSE (LLM) → évalue réponse
5. DECISION → continue ou pas?
6. EVAL_FINAL (LLM) → score + recommandation

---

## 🎯 Commande Finale

**Pour tout lancer:**

```bash
cd c:\Users\nourg\Desktop\nlpcvfinal && python main.py
```

---

**C'est tout! Le projet est prêt. 🚀**
