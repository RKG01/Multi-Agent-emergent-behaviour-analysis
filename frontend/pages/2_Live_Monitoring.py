from typing import Any, Dict, List

import streamlit as st

from utils.api_client import fetch_logs
from utils.config import get_api_base_url, init_session_state


st.title("Live Agent Monitoring")
init_session_state()

base_url = get_api_base_url()
last_response = st.session_state.get("last_response")
request_id = st.text_input(
    "Request ID",
    value=st.session_state.get("last_request_id", ""),
)

if last_response:
    st.subheader("Agent Reports (Last Run)")
    reports = last_response.get("agent_reports", {})
    rows: List[Dict[str, Any]] = []
    for name, report in reports.items():
        rows.append(
            {
                "agent": name,
                "label": report.get("decision_label"),
                "risk": report.get("fraud_risk"),
                "confidence": report.get("confidence"),
            }
        )
    if rows:
        st.table(rows)

if st.button("Refresh Logs") and request_id:
    logs, error = fetch_logs(base_url, request_id=request_id, agent_name=None, limit=100)
    if error:
        st.error(error)
    else:
        st.subheader("Agent Logs")
        st.dataframe(logs, use_container_width=True)
