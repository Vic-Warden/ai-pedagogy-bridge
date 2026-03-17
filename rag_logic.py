import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import Chroma
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

# Shared LLM instance
OLLAMA_MODEL = "llama3.2"
EMBED_MODEL = "nomic-embed-text"

EXERCISES_PDF = "course_materials/exercices.pdf"


def _get_llm():
    return ChatOllama(model=OLLAMA_MODEL, temperature=0)


def _get_embeddings():
    return OllamaEmbeddings(model=EMBED_MODEL)

# Build the full RAG chain from the course PDF
def initialiser_cerveau_ia(chemin_pdf):
    documents = PyPDFLoader(chemin_pdf).load()
    splits = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200
    ).split_documents(documents)

    vectorstore = Chroma.from_documents(documents=splits, embedding=_get_embeddings())
    retriever = vectorstore.as_retriever()

    llm = _get_llm()

    system_prompt = (
        "Tu es un assistant pédagogique. Ton but est d'aider l'étudiant à comprendre son cours. "
        "RÈGLE 1 : Utilise UNIQUEMENT le contexte fourni pour répondre. "
        "RÈGLE 2 : Si la réponse n'est pas dans le contexte, dis honnêtement que tu ne sais pas. "
        "RÈGLE 3 : Ne donne pas la réponse toute faite. Guide l'étudiant pour le faire réfléchir. "
        "\n\n{context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)

# Send a student question through the RAG chain
def poser_question_a_lia(rag_chain, question_eleve):
    return rag_chain.invoke({"input": question_eleve})["answer"]

# Build a RAG chain over the exercises PDF
def initialiser_cerveau_exercices():
    if not os.path.exists(EXERCISES_PDF):
        return None

    documents = PyPDFLoader(EXERCISES_PDF).load()
    splits = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200
    ).split_documents(documents)

    vectorstore = Chroma.from_documents(documents=splits, embedding=_get_embeddings())
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = _get_llm()

    system_prompt = (
        "Tu es un assistant pédagogique. À partir du recueil d'exercices ci-dessous, "
        "propose les exercices les plus pertinents pour aider l'étudiant à travailler "
        "les notions sur lesquelles il a des difficultés. "
        "Indique le numéro de l'exercice, la page si possible, et explique brièvement "
        "pourquoi cet exercice est utile pour sa question. "
        "Réponds en français.\n\n{context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)

# Suggest exercises from the exercise PDF based on student questions
def suggerer_exercices(exercice_chain, questions):
    if exercice_chain is None:
        return "Le fichier d'exercices n'est pas disponible."

    questions_text = "\n".join(f"- {q}" for q in questions)
    query = (
        f"Voici les questions que l'étudiant a posées :\n{questions_text}\n\n"
        "Propose les exercices les plus adaptés pour travailler ces points."
    )
    return exercice_chain.invoke({"input": query})["answer"]


# Generate a revision sheet summarizing all student questions
def generer_fiche_revision(questions):
    llm = _get_llm()

    questions_text = "\n".join(f"- {q}" for q in questions)
    prompt = (
        "Tu es un assistant pédagogique expert. Un étudiant a posé les questions suivantes "
        "pendant sa session d'étude :\n\n"
        f"{questions_text}\n\n"
        "Génère une **fiche de révision** structurée et claire qui :\n"
        "1. Regroupe les questions par thème/notion\n"
        "2. Pour chaque thème, donne un rappel de cours concis\n"
        "3. Liste les points clés à retenir\n"
        "4. Propose des astuces ou moyens mnémotechniques\n"
        "Formate en Markdown avec des titres, listes et emojis."
    )
    return llm.invoke(prompt).content

# Analyze all student questions and produce a teacher synthesis report
def generer_synthese_enseignant(df):
    llm = _get_llm()

    questions_list = df["Question posée"].tolist()
    notions_list = df["Chapitre/Notion"].tolist()
    eleves_list = df["Élève"].tolist() if "Élève" in df.columns else ["Inconnu"] * len(df)

    data_text = "\n".join(
        f"- [{eleve}] [{notion}] {question}"
        for eleve, notion, question in zip(eleves_list, notions_list, questions_list)
    )

    prompt = (
        "Tu es un expert en analyse pédagogique. Voici l'ensemble des questions posées "
        "par les étudiants sur un chapitre de mathématiques. "
        "Chaque ligne contient le nom de l'élève, la notion et la question :\n\n"
        f"{data_text}\n\n"
        "Produis un **rapport de synthèse pour l'enseignant** qui comprend :\n"
        "1. **Vue d'ensemble** : quelles notions posent le plus de problèmes ?\n"
        "2. **Analyse par élève** : quels élèves semblent le plus en difficulté et sur quoi ?\n"
        "3. **Analyse thématique** : pour chaque notion identifiée, décris le type de difficulté "
        "(compréhension, méthode, vocabulaire, etc.)\n"
        "4. **Signaux faibles** : questions atypiques, élèves qui posent la même question "
        "plusieurs fois, erreurs récurrentes à surveiller\n"
        "5. **Recommandations** : actions concrètes pour le prochain cours "
        "(exercices à refaire, points à ré-expliquer, activités suggérées, "
        "élèves à accompagner en priorité)\n"
        "Formate en Markdown, sois concis et actionnable."
    )
    return llm.invoke(prompt).content

# Deep-dive analysis on a single notion for the teacher
def analyser_notion_profonde(notion, questions):
    llm = _get_llm()

    questions_text = "\n".join(f"- {q}" for q in questions)
    prompt = (
        f"Tu es un expert en didactique des mathématiques au lycée.\n"
        f"La notion suivante pose problème aux élèves : **{notion}**\n\n"
        f"Voici les questions posées par les élèves sur cette notion :\n{questions_text}\n\n"
        "Produis une analyse détaillée comprenant :\n"
        "1. **Diagnostic** : quel type de difficulté est en jeu ? "
        "(prérequis manquant, erreur de méthode, confusion de vocabulaire, blocage conceptuel)\n"
        "2. **Activité de remédiation** : propose une activité concrète (10-15 min) à faire en classe\n"
        "3. **Exercice progressif** : propose un exercice en 3 étapes (guidé → semi-guidé → autonome)\n"
        "4. **Erreurs typiques** : liste les erreurs les plus fréquentes des élèves sur cette notion\n"
        "5. **Conseil d'enseignement** : une astuce pédagogique pour mieux expliquer cette notion\n"
        "Formate en Markdown."
    )
    return llm.invoke(prompt).content

# Generate creative ideas
def generer_challenges_pedagogiques():
    llm = _get_llm()

    prompt = (
        "Tu es un game designer pédagogique spécialisé dans la gamification de l'enseignement "
        "des mathématiques au lycée.\n\n"
        "Un enseignant utilise une plateforme d'IA pédagogique qui permet aux élèves de :\n"
        "- Poser des questions sur le cours via un chatbot IA\n"
        "- Générer des fiches de révision personnalisées\n"
        "- Recevoir des exercices adaptés à leurs difficultés\n\n"
        "Invente **5 défis/challenges créatifs format gaming** pour motiver les élèves et "
        "rendre les maths plus engageantes. Pour chaque défi :\n"
        "- **Nom du défi** : un nom fun et accrocheur\n"
        "- **Format** : durée, contexte (en classe, à la maison, en équipe, solo)\n"
        "- **Règles du jeu** : étapes claires et simples\n"
        "- **Système de points/récompenses** : comment on gagne, badges, niveaux\n"
        "- **Variante avancée** : comment corser le défi pour les meilleurs\n"
        "- **Compétence travaillée** : ce que l'élève développe en jouant\n\n"
        "Sois inventif, inspiré par les jeux vidéo, les escape games, les quiz TV, etc. "
        "Formate en Markdown avec des emojis."
    )
    return llm.invoke(prompt).content