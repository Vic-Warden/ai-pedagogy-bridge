import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px
import rag_logic

LOG_FILE = "questions_log.csv"

# Load question log and add computed columns
def _load_data():
    if not os.path.exists(LOG_FILE):
        return None
    df = pd.read_csv(LOG_FILE)
    if df.empty:
        return None

    # Parse dates robustly
    df["Datetime"] = pd.to_datetime(df["Date"], format="%d/%m/%Y %H:%M", errors="coerce")
    df["Jour"] = df["Datetime"].dt.date

    # Backwards-compat: if old CSV has no Élève column, add default
    if "Élève" not in df.columns:
        df.insert(1, "Élève", "Inconnu")

    return df


def show_teacher_space():
    st.header("Tableau de Bord Enseignant")
    st.caption("Vue complète des interactions étudiant, analyses IA et recommandations pédagogiques.")

    df = _load_data()
    if df is None:
        st.info("Aucune question pour le moment. Les données apparaîtront ici quand les élèves utiliseront la plateforme.")
        return

    # ── Tabs (3 tabs: Dashboard, Synthèse IA, Défis Pédagogiques) ──
    tab_dashboard, tab_synthese, tab_challenges = st.tabs([
        "Dashboard", "Synthèse IA", "Conseils Pédagogiques"
    ])

    with tab_dashboard:
        _render_dashboard(df)

    with tab_synthese:
        _render_synthese(df)

    with tab_challenges:
        _render_challenges()

# KPIs + interactive charts + student-level view
def _render_dashboard(df):
    st.subheader("Indicateurs Clés")

    total_q = len(df)
    unique_notions = df["Chapitre/Notion"].nunique()
    top_notion = df["Chapitre/Notion"].mode()[0]
    unique_students = df["Élève"].nunique()

    duplicates = df["Question posée"].value_counts()
    repeated_count = int((duplicates > 1).sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Questions", total_q)
    c2.metric("Élèves Actifs", unique_students)
    c3.metric("Notions Couvertes", unique_notions)
    c4.metric("Notion #1", top_notion)
    c5.metric("Questions Répétées", repeated_count, help="Questions posées plus d'une fois")

    st.divider()

    # Charts: frequency of questions by notion + distribution of questions by notion
    col_bar, col_pie = st.columns(2)

    notion_counts = df["Chapitre/Notion"].value_counts().reset_index()
    notion_counts.columns = ["Notion", "Nombre"]

    with col_bar:
        st.markdown("#### Fréquence des Difficultés par Notion")
        fig_bar = px.bar(
            notion_counts,
            x="Nombre", y="Notion",
            orientation="h",
            color="Nombre",
            color_continuous_scale="Reds",
            text="Nombre",
        )
        fig_bar.update_layout(
            yaxis=dict(autorange="reversed"),
            showlegend=False,
            height=350,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        fig_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_pie:
        st.markdown("#### Répartition des Questions")
        fig_pie = px.pie(
            notion_counts,
            values="Nombre", names="Notion",
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4,
        )
        fig_pie.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # Questions by student
    st.markdown("#### Questions par Élève")

    student_counts = df.groupby("Élève").agg(
        Nb_questions=("Question posée", "size"),
        Notions=("Chapitre/Notion", "nunique"),
    ).reset_index().sort_values("Nb_questions", ascending=False)
    student_counts.columns = ["Élève", "Nb Questions", "Notions touchées"]

    col_table, col_chart = st.columns([1, 1])
    with col_table:
        st.dataframe(student_counts, use_container_width=True, hide_index=True)
    with col_chart:
        fig_stu = px.bar(
            student_counts,
            x="Nb Questions", y="Élève",
            orientation="h",
            color="Nb Questions",
            color_continuous_scale="Teal",
            text="Nb Questions",
        )
        fig_stu.update_layout(
            yaxis=dict(autorange="reversed"),
            showlegend=False,
            height=max(200, len(student_counts) * 50),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        fig_stu.update_traces(textposition="outside")
        st.plotly_chart(fig_stu, use_container_width=True)

    st.divider()

    # Filter by student
    st.markdown("#### Détail par Élève")
    students_list = ["Tous les élèves"] + sorted(df["Élève"].unique().tolist())
    selected_student = st.selectbox("Filtrer par élève :", students_list, key="filter_student")

    if selected_student != "Tous les élèves":
        display_df = df[df["Élève"] == selected_student]
    else:
        display_df = df

    st.dataframe(
        display_df[["Date", "Élève", "Chapitre/Notion", "Question posée"]],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # Signaux faibles
    st.markdown("#### Questions Répétées")

    repeated = duplicates[duplicates > 1].reset_index()
    repeated.columns = ["Question", "Occurrences"]
    if repeated.empty:
        st.success("Aucune question n'a été posée en doublon.")
    else:
        st.dataframe(repeated, use_container_width=True, hide_index=True)

    st.divider()

    # Export
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        csv_data = display_df[["Date", "Élève", "Chapitre/Notion", "Question posée"]].to_csv(index=False).encode("utf-8")
        st.download_button(
            "Exporter en CSV",
            data=csv_data,
            file_name=f"questions_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    with col_dl2:
        md_lines = ["# Journal des Questions Étudiants\n"]
        for eleve, group in display_df.groupby("Élève"):
            md_lines.append(f"\n## {eleve}\n")
            for _, row in group.iterrows():
                md_lines.append(f"- [{row['Date']}] **{row['Chapitre/Notion']}** — {row['Question posée']}")
        md_export = "\n".join(md_lines)
        st.download_button(
            "Exporter en Markdown",
            data=md_export,
            file_name=f"questions_export_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
        )


# AI-generated synthesis and recommendations
def _render_synthese(df):
    st.subheader("Synthèse et Recommandations par l'IA")
    st.caption(
        "L'IA analyse l'ensemble des questions pour produire un rapport actionnable : "
        "notions critiques et recommandations concrètes pour votre prochain cours."
    )

    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.info(f"**{len(df)} questions** de **{df['Élève'].nunique()} élèves** sur **{df['Chapitre/Notion'].nunique()} notions** seront analysées.")
    with col_btn:
        generate = st.button("Générer la synthèse", type="primary", key="btn_synthese")

    if generate:
        with st.spinner("L'IA analyse les données… (cela peut prendre 30-60 secondes)"):
            synthese = rag_logic.generer_synthese_enseignant(df)
        st.session_state.teacher_synthese = synthese

    if "teacher_synthese" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state.teacher_synthese)

        st.download_button(
            "Télécharger le rapport (.md)",
            data=st.session_state.teacher_synthese,
            file_name=f"synthese_enseignant_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            key="dl_synthese",
        )


# Creative pedagogical ideas in a gaming / challenge format
def _render_challenges():

    st.subheader("Défis & Challenges Pédagogiques")
    st.caption(
        "L'IA génère des idées créatives format gaming pour rendre vos cours vivants, "
        "motiver les élèves et intégrer la plateforme au quotidien du lycée."
    )

    if st.button("Générer des défis créatifs", type="primary", key="btn_challenges"):
        with st.spinner("L'IA conçoit des défis créatifs…"):
            challenges_ia = rag_logic.generer_challenges_pedagogiques()
        st.session_state.teacher_challenges = challenges_ia

    if "teacher_challenges" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state.teacher_challenges)

        st.download_button(
            "Télécharger les défis (.md)",
            data=st.session_state.teacher_challenges,
            file_name="defis_pedagogiques.md",
            mime="text/markdown",
            key="dl_challenges",
        )