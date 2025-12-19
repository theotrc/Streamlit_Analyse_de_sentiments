import streamlit as st
import requests
from dotenv import load_dotenv
import os 

load_dotenv(overide=True)

API_URL = os.environ.get("API_URL")

st.set_page_config(page_title="Analyse de sentiment", layout="centered")

st.title("Analyse de sentiment")

st.markdown("Entrez un texte ci-dessous puis cliquez sur 'Envoyer' pour obtenir une prédiction depuis l'API.")

with st.form(key="predict_form"):
    text = st.text_area("Texte à analyser", height=200)
    submitted = st.form_submit_button("Envoyer")

if submitted:
    if not text or text.strip() == "":
        st.warning("Veuillez entrer du texte avant d'envoyer.")
    else:
        with st.spinner("Envoi du texte à l'API..."):
            try:
                resp = requests.post(API_URL, json={"text": text}, timeout=15)
                resp.raise_for_status()
                try:
                    data = resp.json()
                except ValueError:
                    st.error("Réponse invalide de l'API (JSON attendu).")
                    st.write(resp.text)
                else:
                    st.success("Réponse reçue")
                    st.json(data)
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur lors de l'appel à l'API: {e}")
