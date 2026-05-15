import json
from typing import Any, Dict, List

import streamlit as st

from utils.api_client import analyze_claim
from utils.config import get_api_base_url, init_session_state


st.title("Upload Claim")
init_session_state()

base_url = get_api_base_url()

# Use the form object directly for consistent Streamlit behavior.
form = st.form("claim_form")
form.subheader("Claim Details")
claim_id = form.text_input("Claim ID", value="C-001")
amount = form.number_input("Claim Amount", min_value=0.0, value=1000.0, step=100.0)

form.subheader("Claimant")
claimant_name = form.text_input("Claimant Name", value="Test User")
history_count = form.number_input("Prior Claims", min_value=0, value=0, step=1)

form.subheader("Policy")
policy_id = form.text_input("Policy ID", value="P-001")
coverage_limit = form.number_input("Coverage Limit", min_value=0.0, value=10000.0)
deductible = form.number_input("Deductible", min_value=0.0, value=500.0)

form.subheader("Incident")
incident_date = form.text_input("Incident Date", value="2026-05-01")
incident_type = form.text_input("Incident Type", value="collision")
incident_description = form.text_area("Incident Description", value="Rear-end collision")

form.subheader("Documents")
doc_count = form.number_input("Document Count", min_value=0, max_value=5, value=1, step=1)

documents: List[Dict[str, Any]] = []
for idx in range(int(doc_count)):
    form.markdown(f"**Document {idx + 1}**")
    doc_id = form.text_input(f"Document ID {idx + 1}", value=f"D-{idx + 1}")
    filename = form.text_input(f"Filename {idx + 1}", value=f"doc_{idx + 1}.txt")
    text = form.text_area(f"Document Text {idx + 1}", value="Sample text")
    metadata_text = form.text_area(f"Metadata JSON {idx + 1}", value="{}")
    documents.append(
        {
            "document_id": doc_id,
            "filename": filename,
            "text": text,
            "metadata": metadata_text,
        }
    )

submitted = form.form_submit_button("Analyze Claim")

if submitted:
    parsed_documents = []
    for doc in documents:
        try:
            metadata = json.loads(doc["metadata"])
        except json.JSONDecodeError:
            st.error("Metadata JSON is invalid. Please fix the document metadata.")
            st.stop()
        parsed_documents.append(
            {
                "document_id": doc["document_id"],
                "filename": doc["filename"],
                "text": doc["text"],
                "metadata": metadata,
            }
        )

    payload = {
        "claim_id": claim_id,
        "claimant": {"name": claimant_name, "history_count": int(history_count)},
        "policy": {
            "policy_id": policy_id,
            "coverage_limit": float(coverage_limit),
            "deductible": float(deductible),
        },
        "incident": {
            "date": incident_date,
            "type": incident_type,
            "description": incident_description,
        },
        "amount": float(amount),
        "documents": parsed_documents,
    }

    response, error = analyze_claim(base_url, payload)
    if error:
        st.error(error)
    else:
        st.session_state["last_response"] = response
        st.session_state["last_request_id"] = response.get("request_id")
        st.success("Analysis complete")
        st.json(response)
