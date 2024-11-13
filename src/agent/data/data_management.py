import logging
from src.agent.data.data_loader import load_documents
from src.agent.data.vector_store import create_vectorstore_and_retriever

def load_and_prepare_data(accounts_to_load):
    logging.info("Loading data...")
    data = load_documents(accounts_to_load)
    if not data:
        logging.warning("No data loaded. Returning None.")
        return None
    logging.info("Creating vectorstore and retriever...")
    retriever = create_vectorstore_and_retriever(data)
    return retriever
