# src/agent/data/data_loader.py

import os
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.agent.data.tweet_preprocessor import load_and_process_tweets
from langchain.schema import Document  # Added import

def load_documents(tw_accounts):
    docs = []
    for tw_account_folder in tw_accounts:
        folder_path = os.path.join('data', 'NEARMobileAppFollowedAccounts', tw_account_folder)
        if os.path.isdir(folder_path):
            logging.info(f"Loading data from {folder_path}")
            file_count = 0
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith('.json'):
                        file_count += 1
                        full_path = os.path.join(root, file)
                        logging.info(f"Processing file: {full_path}")
                        tweets = load_and_process_tweets(full_path)
                        docs.extend(tweets)
            if file_count == 0:
                logging.warning(f"No JSON files found in {folder_path}")
        else:
            logging.warning(f"Folder {folder_path} does not exist.")

    if not docs:
        logging.warning("No documents found for the specified team folders.")
    else:
        logging.info(f"Loaded {len(docs)} documents from account folders.")

    # Text splitting
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=250, chunk_overlap=0
    )

    # Join the list of tweets and split
    combined_text = "\n".join(docs)
    doc_splits = text_splitter.split_text(combined_text)

    # Convert each split text into a Document object
    document_objects = [Document(page_content=split) for split in doc_splits]  # Added conversion

    return document_objects  # Return Document objects
