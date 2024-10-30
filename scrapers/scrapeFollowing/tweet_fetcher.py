import requests
import os
import yaml
import time
import logging
import json
from dotenv import load_dotenv
from tweet_service import setup_logging, ensure_data_directory, save_followed_accounts

def load_config():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(dir_path, 'tweet_fetcher_config.yaml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def save_state(state, api_calls_count, records_fetched, followed_accounts):
    state_data = {
        'last_known_state': state,
        'api_calls_count': api_calls_count,
        'records_fetched': records_fetched,
        'followed_accounts_sample': followed_accounts[:7]  # Save a sample for visibility
    }
    with open('last_known_state_detailed.json', 'w') as f:
        json.dump(state_data, f, indent=4)

def load_state():
    try:
        with open('last_known_state_detailed.json', 'r') as f:
            return json.load(f).get('last_known_state', {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def exponential_backoff(attempt, base=60):
    return base * (2 ** attempt)  # Exponential backoff

def fetch_followed_accounts(config):
    account = config['account']
    logging.info(f"Fetching followed accounts for: {account}")

    api_calls_count = 0
    records_fetched = 0
    followed_accounts = []
    cursor = -1  # Default cursor to start pagination

    success = False
    attempts = 0

    while not success and attempts < config['max_retries']:
        # Construct URL with query parameters
        url = f"{config['api_endpoint']}?screen_name={account}&count={config['count_per_request']}&cursor={cursor}"

        try:
            # Perform GET request
            response = requests.get(
                url,
                headers=config['headers'],
                timeout=config['request_timeout']
            )
            api_calls_count += 1

            if response.status_code == 200:
                response_data = response.json()
                if response_data and 'users' in response_data:
                    users = response_data['users']
                    followed_accounts.extend(users)
                    num_followed = len(users)
                    records_fetched += num_followed
                    logging.info(f"Fetched {num_followed} followed accounts for {account}.")

                    # Update cursor for pagination
                    cursor = response_data.get('next_cursor', 0)
                    
                    # Stop if there are no more users to fetch
                    if cursor == 0:
                        success = True
                else:
                    logging.warning(f"No followed accounts fetched for {account}. Retrying after delay...")
                    time.sleep(config['request_delay'])
                    attempts += 1
            elif response.status_code == 429 or response.status_code == 500:
                if response.status_code == 429:
                    logging.warning("Rate-limited. Retrying after delay...")
                    time.sleep(exponential_backoff(attempts, base=config['retry_delay']))
                    attempts += 1
                elif response.status_code == 500:
                    logging.warning("500 Error. Retrying after delay...")
                    time.sleep(exponential_backoff(attempts, base=config['request_delay']))
                    attempts += 1
            else:
                logging.error(f"Failed to fetch followed accounts: {response.status_code}")
                break

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            time.sleep(exponential_backoff(attempts, base=config['retry_delay']))
            attempts += 1

    if not success:
        logging.error(f"Failed after {attempts} attempts for {account}")

    # Save the followed accounts
    ensure_data_directory(config['data_directory'])
    save_followed_accounts(followed_accounts, config['data_directory'], account)

    # Save the state if necessary
    save_state({'account': account}, api_calls_count, records_fetched, followed_accounts)

    logging.info(f"Finished fetching followed accounts for {account}. Total API calls: {api_calls_count}. Total records fetched: {records_fetched}")

if __name__ == "__main__":
    load_dotenv()
    config = load_config()
    setup_logging(config['log_level'], config['log_format'])
    fetch_followed_accounts(config)
