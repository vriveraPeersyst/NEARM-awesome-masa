import json
import logging
import os
from datetime import datetime

def setup_logging(log_level, log_format):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    logging.basicConfig(level=numeric_level, format=log_format)

def ensure_data_directory(directory):
    os.makedirs(directory, exist_ok=True)

# Updated to save followed accounts
def save_followed_accounts(followed_accounts, data_directory, account_name):
    filename = f'{data_directory}/{account_name}_followed_accounts_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json'
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(followed_accounts, file, ensure_ascii=False, indent=2)
    logging.info(f"Followed accounts saved to {filename}")

# The query function is not used for followed accounts but retained for completeness
def create_tweet_query(account, start_date, end_date):
    return f"(from:{account})"
