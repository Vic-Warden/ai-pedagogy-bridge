import os
import toml
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

# Load API key
try:
    secrets = toml.load("key.toml")
    os.environ["GOOGLE_API_KEY"] = secrets["GOOGLE_API_KEY"]
except Exception as e:
    st.error(f"Erreur key.toml : {e}")


# Build the full RAG chain from a PDF file
def initialiser_cerveau_ia(chemin_pdf):

    # Load & split PDF into chunks
    documents = PyPDFLoader(chemin_pdf).load()
    splits = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200
    ).split_documents(documents)

    # Create vector store from chunks
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
    retriever = vectorstore.as_retriever()

    # Init LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

    # System prompt: answer from context only, guide the student
    system_prompt = (
        "Tu es un assistant pédagogique. Ton but est d'aider l'étudiant à comprendre son cours. "
        "RÈGLE 1 : Utilise UNIQUEMENT le contexte fourni pour répondre. "
        "RÈGLE 2 : Si la réponse n'est pas dans le contexte, dis honnêtement que tu ne sais pas. "
        "RÈGLE 3 : Ne donne pas la réponse toute faite. Guide l'étudiant pour le faire réfléchir. "
        "\n\n"
        "{context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # Assemble retrieval + generation chain
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)


# Send a student question through the RAG chain and return the answer
def poser_question_a_lia(rag_chain, question_eleve):

    # Run the chain and extract the generated answer
    return rag_chain.invoke({"input": question_eleve})["answer"]