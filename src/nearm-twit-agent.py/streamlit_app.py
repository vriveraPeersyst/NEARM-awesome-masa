# src/nearm-twit-agent.py/streamlit_app.py

import sys
import os
from dotenv import load_dotenv
# Load environment variables
load_dotenv()
import logging
import time
import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space


# Adjust the following lines to set up the correct module path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)

# Insert project_root at the beginning of sys.path
sys.path.insert(0, project_root)  # Changed from append to insert

# Optional: Log the current project_root and sys.path for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info(f"Project Root: {project_root}")
logging.info(f"sys.path: {sys.path}")

# Now import the necessary functions from src.agent.rag_agent
from src.agent.rag_agent import get_rag_response, initialize_agent

st.set_page_config(page_title="💬 NEARMobile Twit Cooker", page_icon="💬")

# Initialize the agent only once per session
# @st.cache_resource
def initialize_agent_cached():
    return initialize_agent()  # Call the function to get the graph

# Use the cached agent initialization
graph = initialize_agent_cached()

def get_streaming_rag_response(task: str):
    logging.info(f"Generating tweet for task: {task}")

    # Construct conversation history
    history = ""
    for msg in st.session_state['message_history']:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg["content"]
        history += f"{role}: {content}\n"

    # Call the imported function directly
    response, steps = get_rag_response(graph, task, history)  # Correct function call

    words = response.split()
    for word in words:
        yield word + " "
        time.sleep(0.05)

st.title("💬 NEARMobile Twit Cooker")

st.markdown("""
Welcome to **NEARMobile Twit Cooker**!

I am an assistant specialized in creating **"degen style"** tweets that are both educational and informative. I can help you generate tweets based on NEAR Protocol's Twitter posts and NEARMobile partners. Let's bring your presence in the crypto community to life with fresh and relevant content!
""")

st.markdown("---")

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

def display_chat_history():
    for msg in st.session_state['message_history']:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

display_chat_history()

if prompt := st.chat_input("Enter your task to generate a tweet:"):
    st.session_state.message_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Display thinking animation
        thinking_placeholder = st.empty()
        with thinking_placeholder:
            for i in range(3):
                for dot in [".", "..", "..."]:
                    thinking_placeholder.markdown(f"Thinking{dot}")
                    time.sleep(0.3)
        
        # Start streaming the response
        try:
            for chunk in get_streaming_rag_response(prompt):
                thinking_placeholder.empty()  # Remove thinking animation
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"An error occurred: {e}")

    st.session_state.message_history.append({"role": "assistant", "content": full_response})

add_vertical_space(5)
