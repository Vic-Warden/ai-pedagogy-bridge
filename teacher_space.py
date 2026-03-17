import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import rag_logic

LOG_FILE = "questions_log.csv"



def _load_data():
    """Load question log and add computed columns."""
    if not os.path.exists(LOG_FILE):
        return None
    df = pd.read_csv(LOG_FILE)
    if df.empty:
        return None

    # Parse dates robustly
    df["Datetime"] = pd.to_datetime(df["Date"], format="%d/%m/%Y %H:%M", errors="coerce")
    df["Jour"] = df["Datetime"].dt.date
    df["Heure"] = df["Datetime"].dt.hour
    df["Jour_semaine"] = df["Datetime"].dt.day_name()
    return df


def show_teacher_space():
    st.header("Tableau de Bord Enseignant")
    st.caption("Vue complète des interactions étudiant, analyses IA et recommandations pédagogiques.")

    df = _load_data()
    if df is None:
        st.info("Aucune question pour le moment. Les données apparaîtront ici quand les élèves utiliseront la plateforme.")
        return

    # ── Tabs ──────────────────────────────────────────────────────
    tab_dashboard, tab_synthese, tab_exploration, tab_conseils = st.tabs([
        "Dashboard", "Synthèse IA", "Exploration", "Conseils Pédagogiques"
    ])


    with tab_dashboard:
        _render_dashboard(df)


    with tab_synthese:
        _render_synthese(df)

    with tab_exploration:
        _render_exploration(df)

    with tab_conseils:
        _render_conseils()


def _render_dashboard(df):
    """KPIs + interactive charts."""

    st.subheader("📈 Indicateurs Clés")

    # Row of KPI metrics
    total_q = len(df)
    unique_notions = df["Chapitre/Notion"].nunique()
    top_notion = df["Chapitre/Notion"].mode()[0]
    unique_days = df["Jour"].nunique()
    avg_per_day = round(total_q / max(unique_days, 1), 1)

    # Detect questions asked multiple times 
    duplicates = df["Question posée"].value_counts()
    repeated_count = int((duplicates > 1).sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Questions", total_q)
    c2.metric("Notions Couvertes", unique_notions)
    c3.metric("Notion #1", top_notion)
    c4.metric("Moy./Jour", avg_per_day)
    c5.metric("Questions Répétées", repeated_count, help="Questions posées plus d'une fois")

    st.divider()

    # Bar chart of notions + Pie chart of distribution
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

    # Timeline of questions + Heatmap by hour
    col_timeline, col_heat = st.columns(2)

    with col_timeline:
        st.markdown("#### Chronologie des Questions")
        timeline = df.groupby("Jour").size().reset_index(name="Questions")
        fig_line = px.area(
            timeline,
            x="Jour", y="Questions",
            markers=True,
            color_discrete_sequence=["#636EFA"],
        )
        fig_line.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_line, use_container_width=True)

    with col_heat:
        st.markdown("#### Activité par Heure")
        hourly = df.groupby("Heure").size().reset_index(name="Questions")
        all_hours = pd.DataFrame({"Heure": range(24)})
        hourly = all_hours.merge(hourly, on="Heure", how="left").fillna(0)
        hourly["Questions"] = hourly["Questions"].astype(int)

        fig_hour = px.bar(
            hourly,
            x="Heure", y="Questions",
            color="Questions",
            color_continuous_scale="Blues",
        )
        fig_hour.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_hour, use_container_width=True)

    st.divider()

    # Weak signals: repeated questions
    st.markdown("#### Signaux Faibles — Questions Répétées")
    st.caption("Les questions posées plusieurs fois peuvent indiquer un blocage ou une frustration.")

    repeated = duplicates[duplicates > 1].reset_index()
    repeated.columns = ["Question", "Occurrences"]
    if repeated.empty:
        st.success("Aucune question n'a été posée en doublon")
    else:
        st.dataframe(repeated, use_container_width=True, hide_index=True)

    st.divider()

    # Full question log with export options
    st.markdown("#### Journal Complet des Questions")
    st.dataframe(df[["Date", "Chapitre/Notion", "Question posée"]], use_container_width=True, hide_index=True)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        csv_data = df[["Date", "Chapitre/Notion", "Question posée"]].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Exporter en CSV",
            data=csv_data,
            file_name=f"questions_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    with col_dl2:
        # Quick Markdown summary for export
        md_lines = ["# Journal des Questions Étudiants\n"]
        for notion, group in df.groupby("Chapitre/Notion"):
            md_lines.append(f"\n## {notion}\n")
            for _, row in group.iterrows():
                md_lines.append(f"- [{row['Date']}] {row['Question posée']}")
        md_export = "\n".join(md_lines)
        st.download_button(
            "⬇️ Exporter en Markdown",
            data=md_export,
            file_name=f"questions_export_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
        )

# AI-generated synthesis and recommendations
def _render_synthese(df):
    st.subheader("Synthèse et Recommandations par l'IA")
    st.caption(
        "L'IA analyse l'ensemble des questions pour produire un rapport actionnable : "
        "notions critiques, signaux faibles, et recommandations concrètes pour votre prochain cours."
    )

    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.info(f"**{len(df)} questions** sur **{df['Chapitre/Notion'].nunique()} notions** seront analysées.")
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

# Per-notion drill-down with AI-powered analysis
def _render_exploration(df):
    st.subheader("Exploration par Notion")
    st.caption(
        "Sélectionnez une notion pour voir les questions associées et obtenir "
        "une analyse IA approfondie avec activités de remédiation."
    )

    notions = sorted(df["Chapitre/Notion"].unique())
    selected = st.selectbox("Choisir une notion :", notions, key="sel_notion")

    filtered = df[df["Chapitre/Notion"] == selected]
    questions = filtered["Question posée"].unique().tolist()

    st.markdown(f"**{len(filtered)} question(s)** posée(s) sur cette notion ({len(questions)} unique(s)).")

    with st.expander("Voir toutes les questions", expanded=True):
        for i, q in enumerate(questions, 1):
            count = int(filtered[filtered["Question posée"] == q].shape[0])
            badge = f" *(×{count})*" if count > 1 else ""
            st.markdown(f"{i}. {q}{badge}")

    if st.button(f"Analyse IA approfondie : {selected}", type="primary", key="btn_deep"):
        with st.spinner("Analyse en cours…"):
            analysis = rag_logic.analyser_notion_profonde(selected, questions)
        st.session_state[f"deep_{selected}"] = analysis

    if f"deep_{selected}" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state[f"deep_{selected}"])

        st.download_button(
            f"Télécharger l'analyse ({selected})",
            data=st.session_state[f"deep_{selected}"],
            file_name=f"analyse_{selected.replace(' ', '_').replace('/', '-')}.md",
            mime="text/markdown",
            key=f"dl_deep_{selected}",
        )

# Creative pedagogical tips for platform integration
def _render_conseils():
    st.subheader("Idées d'Intégration Pédagogique")
    st.caption(
        "Découvrez des scénarios concrets et créatifs pour exploiter cette plateforme "
        "dans votre quotidien au lycée : en cours, en AP, en devoir maison…"
    )

    # Static quick-start tips (always visible)
    st.markdown("### Démarrage Rapide")
    tips = [
        ("En début de cours", "Projetez le dashboard 2 min : montrez la notion #1 et annoncez qu'elle sera retravaillée."),
        ("Pendant l'AP", "Laissez les élèves utiliser le chatbot en autonomie, puis consultez la synthèse IA pour un bilan."),
        ("En devoir maison", "Demandez aux élèves de poser au moins 3 questions sur le cours avant le prochain TD."),
        ("En conseil de classe", "Exportez la synthèse IA comme support objectif des difficultés de la classe."),
    ]
    cols = st.columns(2)
    for i, (title, desc) in enumerate(tips):
        with cols[i % 2]:
            st.markdown(f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem; border-radius: 12px; color: white; margin-bottom: 0.8rem;">
    <strong>{title}</strong><br/>
    <span style="font-size:0.9rem">{desc}</span>
</div>""", unsafe_allow_html=True)

    st.divider()

    # AI-generated advanced scenarios
    st.markdown("### 🤖 Scénarios Avancés générés par l'IA")
    if st.button("✨ Générer des idées créatives", type="primary", key="btn_conseils"):
        with st.spinner("L'IA imagine des scénarios d'usage…"):
            conseils = rag_logic.generer_conseils_pedagogiques()
        st.session_state.teacher_conseils = conseils

    if "teacher_conseils" in st.session_state:
        st.markdown(st.session_state.teacher_conseils)

        st.download_button(
            "Télécharger les conseils (.md)",
            data=st.session_state.teacher_conseils,
            file_name="conseils_pedagogiques.md",
            mime="text/markdown",
            key="dl_conseils",
        )