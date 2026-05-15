import streamlit as st

from utils.api_client import health_check
from utils.config import get_api_base_url, init_session_state


st.set_page_config(page_title="Emergent Fraud Lab", layout="wide")
init_session_state()

st.sidebar.title("Settings")
api_base_url = st.sidebar.text_input("API Base URL", value=get_api_base_url())
st.session_state["api_base_url"] = api_base_url

if st.sidebar.button("Check API Health"):
    data, error = health_check(api_base_url)
    if error:
        st.sidebar.error(error)
    else:
        st.sidebar.success(f"API OK ({data.get('status', 'unknown')})")

st.title("Emergent Fraud Lab")
st.markdown(
    "Use the pages on the left to upload claims, monitor agent activity, and review results."
)
