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
SIGNALS_FILE = "signals_log.csv"

# Number of questions before unlocking the red SOS button
SOS_THRESHOLD = 3


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


# Save a student signal (yellow or red) to the teacher
def sauvegarder_signal(niveau, message, identite):
    """niveau: 'jaune' or 'rouge'"""
    file_exists = os.path.isfile(SIGNALS_FILE)
    with open(SIGNALS_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date", "Élève", "Niveau", "Message", "Nb Questions"])
        nb_q = len(get_student_questions())
        writer.writerow([
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            identite,
            niveau,
            message,
            nb_q,
        ])


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


# Show 
def show_student_space():
    st.header("Espace Étudiant")

    if "student_name" not in st.session_state:
        st.session_state.student_name = ""
    if "student_identified" not in st.session_state:
        st.session_state.student_identified = False
    if "yellow_sent" not in st.session_state:
        st.session_state.yellow_sent = False
    if "red_sent" not in st.session_state:
        st.session_state.red_sent = False
    if "show_red_form" not in st.session_state:
        st.session_state.show_red_form = False

    # Optional identification at start 
    if not st.session_state.student_identified:
        _render_identification()
        return

    # Show who's connected
    if st.session_state.student_name:
        st.caption(f"Connecté(e) en tant que **{st.session_state.student_name}**")
    else:
        st.caption("Mode **anonyme** — tu peux t'identifier à tout moment via le bouton 🔴")

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

    # Tabs
    tab_cours, tab_revision, tab_exercices = st.tabs([
        "Cours & Chat", "Fiche de Révision", "Exercices Suggérés"
    ])

    with tab_cours:
        _render_cours_chat()

    with tab_revision:
        _render_revision()

    with tab_exercices:
        _render_exercices()

# Optional identification screen
def _render_identification():
    st.markdown("---")
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Bienvenue !")
        st.markdown(
            "Tu peux entrer ton prénom pour que le professeur puisse t'aider personnellement, "
            "ou continuer en **anonyme** c'est toi qui choisis."
        )
        with st.form("id_form"):
            name = st.text_input("Ton prénom (facultatif) :", placeholder="Ex : Marie")
            col_a, col_b = st.columns(2)
            with col_a:
                go_named = st.form_submit_button("Valider mon prénom", type="primary")
            with col_b:
                go_anon = st.form_submit_button("Continuer en anonyme")

            if go_named:
                st.session_state.student_name = name.strip() if name.strip() else ""
                st.session_state.student_identified = True
                st.rerun()
            if go_anon:
                st.session_state.student_name = ""
                st.session_state.student_identified = True
                st.rerun()

    with col_right:
        st.markdown("")
        st.markdown("")
        st.info("🔒 Tes questions restent **privées**. Le professeur voit les thèmes, pas tes conversations.")


# Course PDF + Chat + SOS buttons
def _render_cours_chat():
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

        # Chat messages
        chat_container = st.container(height=350)
        with chat_container:
            for msg in st.session_state.messages:
                st.chat_message(msg["role"]).write(msg["content"])

        # Chat input
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

        # ── SOS Buttons ──
        st.markdown("---")
        _render_sos_buttons()

# Sos buttons: yellow (1 click) + red (after 3 questions)
def _render_sos_buttons():
    nb_questions = len(get_student_questions())
    identite = st.session_state.student_name if st.session_state.student_name else "Anonyme"

    col_yellow, col_red = st.columns(2)

    # ── 🟡 Yellow: "J'ai du mal" — always available, 1 click, always anonymous ──
    with col_yellow:
        if st.session_state.yellow_sent:
            st.success("🟡 Signal envoyé !")
        else:
            if st.button("🟡 J'ai du mal", key="btn_yellow", use_container_width=True):
                sauvegarder_signal("jaune", "Difficulté signalée (1 clic)", "Anonyme")
                st.session_state.yellow_sent = True
                st.rerun()
            st.caption("1 clic, anonyme. Le prof voit qu'un élève bloque.")

    # ── 🔴 Red: "Besoin d'aide" — unlocked after SOS_THRESHOLD questions ──
    with col_red:
        if st.session_state.red_sent:
            st.success("🔴 Demande envoyée au professeur !")
        elif nb_questions < SOS_THRESHOLD:
            st.button(
                "🔴 Besoin d'aide",
                key="btn_red_locked",
                use_container_width=True,
                disabled=True,
            )
            st.caption(f"Débloqué après {SOS_THRESHOLD} questions ({nb_questions}/{SOS_THRESHOLD})")
        else:
            if not st.session_state.show_red_form:
                if st.button("🔴 Besoin d'aide", key="btn_red", type="primary", use_container_width=True):
                    st.session_state.show_red_form = True
                    st.rerun()
                st.caption("Envoyer un message au prof (anonyme ou avec ton nom)")
            else:
                _render_red_form(identite)


def _render_red_form(identite):
    """Form for the red SOS button — message + choose anonymous or named."""
    with st.container(border=True):
        st.markdown("##### 🔴 Demande d'aide au professeur")

        signal_msg = st.text_area(
            "Décris ta difficulté (facultatif) :",
            placeholder="Ex : Je ne comprends pas les équations quotients…",
            key="red_signal_msg",
        )

        col_anon, col_named = st.columns(2)

        with col_anon:
            if st.button("Envoyer anonymement", key="btn_red_anon", use_container_width=True):
                msg = signal_msg.strip() if signal_msg.strip() else "Besoin d'aide (pas de détail)"
                sauvegarder_signal("rouge", msg, "Anonyme")
                st.session_state.red_sent = True
                st.session_state.show_red_form = False
                st.rerun()

        with col_named:
            name_input = st.text_input(
                "Ton prénom :",
                value=st.session_state.student_name,
                placeholder="Ex : Marie",
                key="red_name_input",
            )
            if st.button("Envoyer avec mon nom", key="btn_red_named", use_container_width=True):
                chosen_name = name_input.strip() if name_input.strip() else "Anonyme"
                if chosen_name != "Anonyme":
                    st.session_state.student_name = chosen_name
                msg = signal_msg.strip() if signal_msg.strip() else "Besoin d'aide (pas de détail)"
                sauvegarder_signal("rouge", msg, chosen_name)
                st.session_state.red_sent = True
                st.session_state.show_red_form = False
                st.rerun()

# Revision sheet tab
def _render_revision():
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

# Exercise suggestions tab
def _render_exercices():
    st.subheader("Exercices Suggérés")
    st.caption("L'IA cherche dans le recueil d'exercices ceux qui correspondent à tes difficultés.")

    questions = get_student_questions()

    if not questions:
        st.info("Pose d'abord des questions dans le chat pour obtenir des suggestions !")
    elif st.session_state.exercice_chain is None:
        st.warning("Le fichier exercices.pdf n'est pas disponible.")
    else:
        st.write(f"**{len(questions)} question(s)** à analyser.")

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