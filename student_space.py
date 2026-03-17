import streamlit as st
import csv
import os
import base64
from datetime import datetime
import rag_logic

# Paths
PDF_PATH = "course_materials/chapitre1.pdf"
EXERCISES_PDF = "course_materials/exercices.pdf"
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


# Log question + detected topic + student name to CSV for teacher dashboard
def sauvegarder_question(question):
    notion = analyser_notion(question)
    eleve = st.session_state.get("student_name", "Anonyme")
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date", "Élève", "Chapitre/Notion", "Question posée"])
        writer.writerow([datetime.now().strftime("%d/%m/%Y %H:%M"), eleve, notion, question])


# Render a PDF inside the Streamlit page via a base64 iframe
def afficher_pdf(chemin_pdf):
    with open(chemin_pdf, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" type="application/pdf"></iframe>',
        unsafe_allow_html=True,
    )


# Get all student questions from this session
def get_student_questions():
    return [
        msg["content"]
        for msg in st.session_state.get("messages", [])
        if msg["role"] == "user"
    ]


def show_student_space():
    st.header("Espace Étudiant")

    # Initialize student name in session state
    if "student_name" not in st.session_state:
        st.session_state.student_name = ""

    if not st.session_state.student_name:
        st.info("Identifie-toi pour commencer !")
        with st.form("student_id_form"):
            name_input = st.text_input("Ton prénom et nom :", placeholder="Ex : Marie Dupont")
            submitted = st.form_submit_button("Valider", type="primary")
            if submitted and name_input.strip():
                st.session_state.student_name = name_input.strip()
                st.rerun()
            elif submitted:
                st.warning("Merci d'entrer ton nom pour continuer.")
        return 

    st.success(f"Connecté(e) en tant que **{st.session_state.student_name}**")

    # Init RAG chains once per session
    if "rag_chain" not in st.session_state:
        if os.path.exists(PDF_PATH):
            with st.spinner("Chargement du cours..."):
                st.session_state.rag_chain = rag_logic.initialiser_cerveau_ia(PDF_PATH)
        else:
            st.error("PDF de cours introuvable.")

    if "exercice_chain" not in st.session_state:
        if os.path.exists(EXERCISES_PDF):
            with st.spinner("Chargement des exercices..."):
                st.session_state.exercice_chain = rag_logic.initialiser_cerveau_exercices()
        else:
            st.session_state.exercice_chain = None

    tab_cours, tab_revision, tab_exercices = st.tabs([
        "Cours & Chat", "Fiche de Révision", "Exercices Suggérés"
    ])

    # Course PDF + Chat
    with tab_cours:
        col_pdf, col_chat = st.columns([1.2, 0.8])

        with col_pdf:
            st.subheader("Support de Cours")
            if os.path.exists(PDF_PATH):
                afficher_pdf(PDF_PATH)
            else:
                st.warning("PDF manquant.")

        with col_chat:
            st.subheader("Assistant Tuteur")

            if "messages" not in st.session_state:
                st.session_state.messages = [
                    {"role": "assistant", "content": "Pose-moi tes questions sur le cours ! 🎓"}
                ]

            chat_container = st.container(height=500)
            with chat_container:
                for msg in st.session_state.messages:
                    st.chat_message(msg["role"]).write(msg["content"])

            if question := st.chat_input("Une notion n'est pas claire ?"):
                st.session_state.messages.append({"role": "user", "content": question})
                sauvegarder_question(question)

                if "rag_chain" in st.session_state:
                    with st.spinner("Réflexion..."):
                        reponse_ia = rag_logic.poser_question_a_lia(
                            st.session_state.rag_chain, question
                        )
                else:
                    reponse_ia = "Cours non chargé."

                st.session_state.messages.append({"role": "assistant", "content": reponse_ia})
                st.rerun()

    # Revision sheet tab
    with tab_revision:
        st.subheader("Fiche de Révision Personnalisée")
        st.caption("L'IA génère une fiche de révision basée sur toutes tes questions.")

        questions = get_student_questions()

        if not questions:
            st.info("Pose d'abord des questions dans le chat pour générer ta fiche !")
        else:
            st.write(f"**{len(questions)} question(s)** posée(s) pendant cette session.")

            if st.button("Générer ma fiche de révision", type="primary", key="btn_revision"):
                with st.spinner("Génération de ta fiche de révision..."):
                    fiche = rag_logic.generer_fiche_revision(questions)
                st.session_state.fiche_revision = fiche

            if "fiche_revision" in st.session_state:
                st.markdown("---")
                st.markdown(st.session_state.fiche_revision)

                st.download_button(
                    label="Télécharger la fiche (.md)",
                    data=st.session_state.fiche_revision,
                    file_name="fiche_revision.md",
                    mime="text/markdown",
                )

    # Exercise suggestions based on student questions
    with tab_exercices:
        st.subheader("Exercices Suggérés")
        st.caption("L'IA cherche dans le recueil d'exercices ceux qui correspondent à tes difficultés.")

        questions = get_student_questions()

        if not questions:
            st.info("Pose d'abord des questions dans le chat pour obtenir des suggestions !")
        elif st.session_state.exercice_chain is None:
            st.warning("Le fichier exercices.pdf n'est pas disponible.")
        else:
            st.write(f"**{len(questions)} question(s)** à analyser.")

            # Show exercise PDF
            with st.expander("Voir le recueil d'exercices"):
                afficher_pdf(EXERCISES_PDF)

            if st.button("Trouver les exercices adaptés", type="primary", key="btn_exercices"):
                with st.spinner("Recherche des exercices les plus pertinents..."):
                    suggestions = rag_logic.suggerer_exercices(
                        st.session_state.exercice_chain, questions
                    )
                st.session_state.exercices_suggeres = suggestions

            if "exercices_suggeres" in st.session_state:
                st.markdown("---")
                st.markdown(st.session_state.exercices_suggeres)