import streamlit as st

from utils.config import init_session_state


st.title("Final Decision")
init_session_state()

last_response = st.session_state.get("last_response")
if not last_response:
    st.info("Run an analysis first to view the final decision.")
    st.stop()

st.subheader("Decision")
st.write(f"Label: {last_response.get('final_label')}")
st.write(f"Score: {last_response.get('final_score')}")

st.subheader("Agent Reports")
st.json(last_response.get("agent_reports", {}))

conflicts = last_response.get("conflicts", [])
if conflicts:
    st.subheader("Conflicts")
    st.dataframe(conflicts, use_container_width=True)
