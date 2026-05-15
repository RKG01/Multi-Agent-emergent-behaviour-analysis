import streamlit as st

from utils.config import init_session_state


st.title("Emergence Analytics")
init_session_state()

last_response = st.session_state.get("last_response")
if not last_response:
    st.info("Run an analysis first to view emergence signals.")
    st.stop()

conflicts = last_response.get("conflicts", [])
redundancy = last_response.get("redundancy")

st.subheader("Conflict Summary")
st.write(f"Conflict count: {len(conflicts)}")
if conflicts:
    st.dataframe(conflicts, use_container_width=True)

st.subheader("Redundancy Summary")
if redundancy:
    st.write(f"Overlap score: {redundancy.get('overlap_score')}")
    duplicated = redundancy.get("duplicated_evidence", [])
    if duplicated:
        st.dataframe(duplicated, use_container_width=True)
else:
    st.info("No redundancy summary available yet.")
