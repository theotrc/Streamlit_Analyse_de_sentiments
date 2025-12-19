# Application Streamlit — Analyse de sentiment

Cette petite application Streamlit permet d'envoyer un texte à l'API `http://127.0.0.1:8000/predict` et d'afficher la réponse JSON.

## Installation

Ouvrez un terminal (PowerShell recommandé) à la racine du projet puis :

```powershell
pip install -r requirements.txt
```

## Lancer l'application

```powershell
streamlit run app.py
```

## Remarques

- L'API doit être accessible à l'adresse `http://127.0.0.1:8000/predict` et accepter un JSON de la forme `{ "text": "..." }`.
- La réponse attendue est au format JSON; le contenu sera affiché tel quel dans l'interface.
