import streamlit as st

from utils.config import init_session_state


st.title("Fraud Dashboard")
init_session_state()

last_response = st.session_state.get("last_response")
if not last_response:
    st.info("Run an analysis first to populate the dashboard.")
    st.stop()

reports = last_response.get("agent_reports", {})
if reports:
    st.subheader("Agent Risk Scores")
    chart_data = {
        name: report.get("fraud_risk", 0.0) for name, report in reports.items()
    }
    st.bar_chart(chart_data)

final_label = last_response.get("final_label")
final_score = last_response.get("final_score")

st.subheader("Final Decision")
st.metric("Label", final_label or "N/A")
st.metric("Score", final_score if final_score is not None else 0.0)
