import streamlit as st
import csv
import os
import base64
from datetime import datetime
import rag_logic

# Path to course PDF & question log
PDF_PATH = "course_materials/chapitre1.pdf"
LOG_FILE = "questions_log.csv"


# Detect which topic the question is about
def analyser_notion(question):
    q = question.lower()
    
    if "produit nul" in q or "facteur" in q or "factoriser" in q:
        return "Théorème du produit nul"
    elif "premier degré" in q or "fondamentale" in q or "règle" in q or "résolution" in q:
        return "Équations fondamentales"
    elif "quotient" in q or "interdite" in q or "dénominateur" in q or "fraction" in q:
        return "Équations quotients"
    elif "carré" in q or "racine" in q or "x2" in q:
        return "Équations du type x²=a"
    elif "définition" in q or "inconnu" in q or "c'est quoi" in q:
        return "Définition d'une équation"
    else:
        return "Méthode générale / Autre"


# Log question + detected topic to CSV for teacher dashboard
def sauvegarder_question(question):
    notion = analyser_notion(question)
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date", "Chapitre/Notion", "Question posée"])
        writer.writerow([datetime.now().strftime("%d/%m/%Y %H:%M"), notion, question])

# Render a PDF inside the Streamlit page via a base64 iframe
def afficher_pdf(chemin_pdf):
    with open(chemin_pdf, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" type="application/pdf"></iframe>',
        unsafe_allow_html=True,
    )


def show_student_space():
    st.header("Espace Étudiant")

    # Init RAG chain once per session
    if "rag_chain" not in st.session_state:
        if os.path.exists(PDF_PATH):
            with st.spinner("Chargement..."):
                st.session_state.rag_chain = rag_logic.initialiser_cerveau_ia(PDF_PATH)
        else:
            st.error("PDF introuvable.")

    # Layout: PDF left, chat right
    col_pdf, col_chat = st.columns([1.2, 0.8])

    with col_pdf:
        st.subheader("Support de Cours")
        if os.path.exists(PDF_PATH):
            afficher_pdf(PDF_PATH)
        else:
            st.warning("PDF manquant.")

    with col_chat:
        st.subheader("💬 Assistant Tuteur")

        # Init chat history
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Pose-moi tes questions sur le cours !"}
            ]

        # Render chat history in a scrollable container
        chat_container = st.container(height=500)
        with chat_container:
            for msg in st.session_state.messages:
                st.chat_message(msg["role"]).write(msg["content"])

        # Handle new question
        if question := st.chat_input("Une notion n'est pas claire ?"):
            st.chat_message("user").write(question)
            st.session_state.messages.append({"role": "user", "content": question})

            # Log question for teacher analytics
            sauvegarder_question(question)

            # Get RAG response (or fallback)
            if "rag_chain" in st.session_state:
                with st.spinner("..."):
                    reponse_ia = rag_logic.poser_question_a_lia(st.session_state.rag_chain, question)
            else:
                reponse_ia = "Cours non chargé."

            st.chat_message("assistant").write(reponse_ia)
            st.session_state.messages.append({"role": "assistant", "content": reponse_ia})