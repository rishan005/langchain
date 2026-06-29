import streamlit as st
import requests

# Configuration
API_URL = "http://localhost:8000" # Ensure your FastAPI app is running here

st.set_page_config(page_title="AI Chatbot", page_icon="🤖")

st.title("🤖 LangChain FastAPI Chatbot")

# --- Authentication State ---
if "username" not in st.session_state:
    st.session_state.username = None

# --- Sidebar / Auth ---
if not st.session_state.username:
    mode = st.sidebar.radio("Mode", ["Login", "Register"])
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Submit"):
        if mode == "Register":
            response = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
            if response.status_code == 200:
                st.success("Registered! Please login.")
            else:
                st.error(response.json().get("detail", "Error"))
        else:
            # Assuming you verify user exists before starting chat
            st.session_state.username = username
            st.rerun()
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
    if st.sidebar.button("Logout"):
        st.session_state.username = None
        st.rerun()

# --- Chat Interface ---
if st.session_state.username:
    # Initialize session state for messages if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle Input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message to UI
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Send to FastAPI
        try:
            response = requests.post(
                f"{API_URL}/{st.session_state.username}/chat",
                json={"message": prompt}
            )
            data = response.json()
            bot_reply = data.get("response", "No response received.")
            
            # Add assistant message to UI
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            with st.chat_message("assistant"):
                st.markdown(bot_reply)
        except Exception as e:
            st.error(f"Could not connect to backend: {e}")