import streamlit as st
import student_space
import teacher_space

# ── Page config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Pedagogy Bridge",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 0.5rem 0 1rem 0;">
            <span style="font-size:2.5rem;">🎓</span>
            <h2 style="margin:0;">AI Pedagogy Bridge</h2>
            <p style="color:gray; font-size:0.85rem; margin-top:0.2rem;">
                Plateforme IA locale · Ollama
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    page = st.radio(
        "Choisissez votre espace :",
        ["🎒 Espace Étudiant", "🎓 Espace Professeur"],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("🔒 100 % local — aucune donnée ne quitte votre machine.")
    st.caption("Propulsé par Ollama · LLaMA 3.2")

# ── Page routing ──────────────────────────────────────────────────
if page == "🎒 Espace Étudiant":
    student_space.show_student_space()
else:
    teacher_space.show_teacher_space()