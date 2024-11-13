# src/agent/data/vector_store.py

from langchain_community.vectorstores import SKLearnVectorStore
from langchain_openai import OpenAIEmbeddings

def create_vectorstore_and_retriever(documents):
    # No need to convert documents if they are already Document objects
    vectorstore = SKLearnVectorStore.from_documents(
        documents=documents,
        embedding=OpenAIEmbeddings(),
    )
    retriever = vectorstore.as_retriever(k=4)
    return retriever