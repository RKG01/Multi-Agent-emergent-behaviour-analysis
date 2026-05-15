import os

import streamlit as st


DEFAULT_API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def init_session_state() -> None:
    # Initialize shared UI state once per session.
    if "api_base_url" not in st.session_state:
        st.session_state["api_base_url"] = DEFAULT_API_BASE_URL
    if "last_response" not in st.session_state:
        st.session_state["last_response"] = None
    if "last_request_id" not in st.session_state:
        st.session_state["last_request_id"] = ""


def get_api_base_url() -> str:
    return st.session_state.get("api_base_url", DEFAULT_API_BASE_URL)
