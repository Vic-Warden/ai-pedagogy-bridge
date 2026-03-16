import streamlit as st
import pandas as pd
import os

LOG_FILE = "questions_log.csv"


def show_teacher_space():
    st.header("Tableau de bord Enseignant — Learning Analytics")

    # Check if student questions exist
    if not os.path.exists(LOG_FILE):
        st.info("Aucune question pour le moment.")
        return

    df = pd.read_csv(LOG_FILE)
    if df.empty:
        st.info("Aucune question pour le moment.")
        return

    # KPIs
    st.subheader("Aperçu de la journée")
    col1, col2 = st.columns(2)
    col1.metric("Questions posées", len(df))
    col2.metric("Notion la plus posée", df["Chapitre/Notion"].mode()[0])

    st.divider()

    # Frequency chart
    st.subheader("Fréquence des incompréhensions")
    st.bar_chart(df["Chapitre/Notion"].value_counts())

    # Full question log
    st.subheader("Signaux faibles")
    st.dataframe(df, use_container_width=True)