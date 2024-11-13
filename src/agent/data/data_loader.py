import os
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.agent.data.tweet_preprocessor import load_and_process_tweets
from langchain.schema import Document
def load_documents(accounts_to_load):
    docs = []
    for account in accounts_to_load:
        folder_path = os.path.join('data', 'NEARMobileAppFollowedAccounts', account)
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
        logging.warning("No documents found for the specified accounts.")
    else:
        logging.info(f"Loaded {len(docs)} documents from account folders.")

    # Text splitting
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=250, chunk_overlap=0
    )

    # Split documents
    split_docs = []
    for doc in docs:
        # Ensure doc is a string
        if isinstance(doc, Document):
            text = doc.page_content
        else:
            text = doc
        splits = text_splitter.split_text(text)
        for split in splits:
            split_docs.append(Document(page_content=split))

    logging.info(f"Total split documents: {len(split_docs)}")
    return split_docs
