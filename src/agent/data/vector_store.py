# #src/agent/data/vector_store.py

# from langchain_community.vectorstores import Annoy
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain.schema import Document
# import logging

# def create_vectorstore_and_retriever(data):
#     if not data:
#         logging.error("No data provided to create vector store.")
#         raise ValueError("No data provided to create vector store.")
#     logging.info(f"Creating vector store with {len(data)} documents.")

#     # Convert text to Document objects
#     documents = [Document(page_content=text) for text in data]

#     # Use a multilingual embeddings model suitable for Spanish
#     embeddings = HuggingFaceEmbeddings(
#         model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
#     )

#     # Pass the embeddings instance directly
#     vectorstore = Annoy.from_documents(
#         documents=documents,
#         embedding=embeddings,
#         n_trees=20
#     )

#     retriever = vectorstore.as_retriever(k=10)
#     return retriever


# src/agent/data/vector_store.py
# src/agent/data/vector_store.py

from langchain_community.embeddings import HuggingFaceEmbeddings # Updated import
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

def create_vectorstore_and_retriever(documents):
    """
    Create vector store and retriever.

    :param documents: The list of Document objects.
    :type documents: List[Document]
    :return: The retriever object.
    :rtype: Retrieval
    """
    # Define tokenizer arguments to avoid the warning
    tokenizer_kwargs = {
        'clean_up_tokenization_spaces': True
    }

    # Initialize embeddings with tokenizer arguments
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={
            'tokenizer_kwargs': tokenizer_kwargs
        }
    )

    # Create the FAISS vector store from Document objects
    vectorstore = FAISS.from_documents(documents, embeddings)

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    return retriever

# # src/data_processing/vector_store.py
# from langchain.vectorstores import FAISS
# from langchain.embeddings import OpenAIEmbeddings
# import os

# def create_vector_store(processed_data_dir):
#     texts = []
#     for filename in os.listdir(processed_data_dir):
#         with open(os.path.join(processed_data_dir, filename), 'r') as file:
#             texts.append(file.read())

#     embeddings = OpenAIEmbeddings()
#     vectorstore = FAISS.from_texts(texts, embeddings)
#     vectorstore.save_local('data/vectorstores/faiss_index')
#     return vectorstore

# # Usage
# vectorstore = create_vector_store('data/processed/')

# # src/agents/retriever_agent.py
# from langchain.vectorstores import FAISS

# def get_retriever(vectorstore_path):
#     vectorstore = FAISS.load_local(vectorstore_path)
#     retriever = vectorstore.as_retriever(search_type="similarity", k=5)
#     return retriever

# # Usage
# retriever = get_retriever('data/vectorstores/faiss_index')

