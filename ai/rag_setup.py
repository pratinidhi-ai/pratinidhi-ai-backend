# ai/rag_setup.py
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import os
load_dotenv()

def create_vectorstore(pdf_path="files/sat_book.pdf"):
    print(f"Loading PDF from: {pdf_path}")
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found at {pdf_path}")

    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    save_path = "files/sat_faiss_index"
    vectorstore.save_local(save_path)
    print(f"Saved FAISS index at {save_path}")

    return vectorstore

def load_vectorstore():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vectorstore = FAISS.load_local("files/sat_faiss_index", embeddings, allow_dangerous_deserialization=True)
    return vectorstore

if __name__ == "__main__":
    create_vectorstore()
