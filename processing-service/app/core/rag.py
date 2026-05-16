import os
import logging
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")
CHROMA_DIR = "/tmp/chroma_db"

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY
)


def build_vectorstore() -> Chroma:
    docs = []
    knowledge_path = os.path.abspath(KNOWLEDGE_DIR)

    if not os.path.exists(knowledge_path):
        logger.warning("Pasta knowledge não encontrada.")
        return Chroma(embedding_function=embeddings, persist_directory=CHROMA_DIR)

    for fname in os.listdir(knowledge_path):
        if fname.endswith(".pdf"):
            path = os.path.join(knowledge_path, fname)
            logger.info(f"Carregando documento: {fname}")
            try:
                loader = PyPDFLoader(path)
                docs.extend(loader.load())
            except Exception as e:
                logger.error(f"Erro ao carregar {fname}: {e}")

    if not docs:
        logger.warning("Nenhum documento PDF encontrado na pasta knowledge.")
        return Chroma(embedding_function=embeddings, persist_directory=CHROMA_DIR)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    logger.info(f"RAG: {len(chunks)} chunks indexados.")

    vectorstore = Chroma.from_documents(
        chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    return vectorstore


def query_knowledge(vectorstore: Chroma, query: str, k: int = 3) -> str:
    if vectorstore is None:
        return "Sem base de conhecimento disponível."
    try:
        docs = vectorstore.similarity_search(query, k=k)
        return "\n\n".join([d.page_content for d in docs])
    except Exception as e:
        logger.error(f"Erro na consulta RAG: {e}")
        return "Erro ao consultar base de conhecimento."