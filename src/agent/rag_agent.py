import logging
from src.agent.data.data_management import load_and_prepare_data
from src.agent.rag.rag_chain_setup import setup_rag_chain
from src.agent.utils import extract_accounts
from src.agent.search_tools.search_tools import get_web_search_tool

def get_rag_response(question: str, history=""):
    logging.info(f"Generating response for question: {question}")

    # Extract relevant accounts from the user's question
    accounts_to_load = extract_accounts(question, history)
    logging.info(f"Accounts extracted: {accounts_to_load}")

    if not accounts_to_load:
        logging.warning("No relevant accounts found. Using default accounts.")
        accounts_to_load = ['NEARMobile_app']  # Use a default account if none found

    # Load data and create retriever dynamically
    retriever = load_and_prepare_data(accounts_to_load)

    # If no retriever could be created (no data loaded), consider handling it
    if retriever is None:
        return "Sorry, I couldn't find any relevant information to generate a tweet.", []

    # Set up RAG chain
    rag_chain = setup_rag_chain()

    # Retrieve documents
    logging.info(f"Retrieving data for question: {question}")
    docs = retriever.get_relevant_documents(question)

    # If no documents found, perform web search
    if not docs:
        logging.info("No relevant documents found in vectorstore, performing web search.")
        web_search_tool = get_web_search_tool()
        web_results = web_search_tool.run(question)
        data_texts = web_results
    else:
        # Prepare data texts from retrieved documents
        data_texts = "\n".join([doc.page_content for doc in docs])

    # Generate response using RAG chain
    response = rag_chain.invoke({"question": question, "data": data_texts, "history": history})

    return response, []
