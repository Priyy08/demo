import requests
import streamlit as st
import json
from utils.constants import API_BASE_URL

def get_auth_headers():
    """Constructs authorization headers with the user's ID token."""
    token = st.session_state.get('id_token')
    
    if not token:
        st.error("Authentication session has expired. Please log in again.")
        return None
        
    return {"Authorization": f"Bearer {token}"}

def fetch_conversations():
    """Fetches all conversations for the current user."""
    auth_headers = get_auth_headers()
    if not auth_headers:
        return []
    try:
        response = requests.get(f"{API_BASE_URL}/conversations/", headers=auth_headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching conversations: {e}")
        return []

def create_new_conversation(title: str):
    """Creates a new conversation."""
    auth_headers = get_auth_headers()
    if not auth_headers:
        return None
    try:
        response = requests.post(
            f"{API_BASE_URL}/conversations/",
            json={"title": title},
            headers=auth_headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating conversation: {e}")
        return None

def rename_conversation(conv_id: str, new_title: str):
    auth_headers = get_auth_headers()
    if not auth_headers: return False
    try:
        response = requests.put(f"{API_BASE_URL}/conversations/{conv_id}", json={"title": new_title}, headers=auth_headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error renaming conversation: {e}")
        return False

def delete_conversation(conv_id: str):
    auth_headers = get_auth_headers()
    if not auth_headers: return False
    try:
        response = requests.delete(f"{API_BASE_URL}/conversations/{conv_id}", headers=auth_headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting conversation: {e}")
        return False

def stream_chat_responses(conv_id: str, message: str):
    """
    Sends a message and streams the response from the backend.
    """
    payload = {"conversation_id": conv_id, "message": message}
    auth_headers = get_auth_headers()
    
    if not auth_headers:
        yield ""
        return

    # Logging has been removed as the issue is resolved.

    try:
        with requests.post(
            f"{API_BASE_URL}/chat/message",
            json=payload,
            headers=auth_headers, 
            stream=True
        ) as r:
            r.raise_for_status()
            for chunk in r.iter_lines():
                if chunk:
                    decoded_chunk = chunk.decode('utf-8')
                    if decoded_chunk.startswith('data:'):
                        try:
                            data_str = decoded_chunk[len('data:'):].strip()
                            data = json.loads(data_str)
                            yield data.get("content", "")
                        except json.JSONDecodeError:
                            continue
                            
    except requests.exceptions.HTTPError as e:
        st.error(f"An error occurred while communicating with the chat API: {e}")
        yield ""
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        yield ""

def register_user(email: str, password: str, display_name: str):
    """Calls the backend to register a new user."""
    try:
        response = requests.post(f"{API_BASE_URL}/auth/register", json={
            "email": email,
            "password": password,
            "display_name": display_name
        })
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        st.error(f"Registration failed: {e.response.json().get('detail', 'Unknown error')}")
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to the server: {e}")
        return False

def logout_user():
    """Calls the backend to log the user out and invalidate their token."""
    auth_headers = get_auth_headers()
    if not auth_headers:
        return False
    try:
        response = requests.post(f"{API_BASE_URL}/auth/logout", headers=auth_headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False
