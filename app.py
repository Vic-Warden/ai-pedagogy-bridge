import streamlit as st
import student_space
import teacher_space

# Page config
st.set_page_config(page_title="AI Pedagogy Bridge", layout="wide")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choisissez votre espace :",
    ["Espace Etudiant", "Espace Professeur"]
)

# Page routing
if page == "Espace Etudiant":
    student_space.show_student_space()

elif page == "Espace Professeur":
    teacher_space.show_teacher_space()