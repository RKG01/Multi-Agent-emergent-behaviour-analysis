# Implementation Guide with Checkpoints
Document date: 2026-05-15
Version: 0.1

This file defines the step-by-step implementation plan with clear checkpoints. Do not proceed beyond a checkpoint without review.

Implementation order (must follow):
1. Backend setup
2. Gemini integration
3. LangGraph setup
4. Single agent
5. Multi-agent workflow
6. Logging system
7. FastAPI endpoints
8. Streamlit frontend
9. Emergence analytics
10. Testing

## Phase 1: Backend Setup
Scope:
- Create backend skeleton (FastAPI app, core config, logging stubs).
- Define Pydantic schemas for requests and agent outputs.
- Create SQLite connection layer (no advanced features yet).

Checkpoint 1 (exit criteria):
- App starts and responds to /health (stub ok).
- Pydantic schemas validate a sample claim payload.
- No LangGraph or Gemini code yet.

## Phase 2: Gemini Integration
Scope:
- Add Gemini client wrapper with retries and JSON-only outputs.
- Add prompt templates for each agent.
- Add response validation utility.

Checkpoint 2:
- A standalone Gemini call returns valid JSON for a sample prompt.
- Invalid JSON triggers retry and logs an error.

## Phase 3: LangGraph Setup
Scope:
- Implement FraudState schema.
- Build a minimal LangGraph with ingest -> single agent -> finalize.
- Add routing counters for loop prevention.

Checkpoint 3:
- LangGraph runs end-to-end with a mock agent output.
- State updates are deterministic and logged.

## Phase 4: Single Agent Implementation
Scope:
- Implement Claim Validator Agent end-to-end.
- Validate inputs, call Gemini, parse output, update state.

Checkpoint 4:
- One real agent report is produced and stored in state.
- Output passes schema validation with confidence in [0,1].

## Phase 5: Multi-Agent Workflow
Scope:
- Add Document Verification, Behavioral Analysis, Anomaly Detection.
- Add Coordinator Agent with conflict and redundancy summaries.

Checkpoint 5:
- All agents run in a single graph execution.
- Coordinator produces a final decision.

## Phase 6: Logging System
Scope:
- Add SQLite tables for claims, agent_logs, emergence_events, metrics.
- Write log events for each node and agent call.

Checkpoint 6:
- Logs are written for a full run.
- Query endpoints can retrieve logs (even if responses are raw).

## Phase 7: FastAPI Endpoints
Scope:
- Implement POST /analyze-claim using the graph.
- Implement GET /logs, GET /metrics, GET /health.

Checkpoint 7:
- /analyze-claim returns structured response.
- /logs and /metrics return recent data.

## Phase 8: Streamlit Frontend
Scope:
- Create upload page and simple results view.
- Add live agent monitoring page.

Checkpoint 8:
- User can upload a claim and see a final decision in UI.
- Basic agent reports visible in a table.

## Phase 9: Emergence Analytics
Scope:
- Compute coordination, conflict, redundancy, loop risk metrics.
- Add emergence events logging and dashboards.

Checkpoint 9:
- Emergence metrics appear in the UI.
- At least one emergence event is logged per run when thresholds are met.

## Phase 10: Testing
Scope:
- Unit tests for schemas and validators.
- Integration tests for workflow and endpoints.
- Edge case tests for missing or conflicting data.

Checkpoint 10:
- All tests pass locally.
- Coverage includes core workflow paths.

## Review Gates (Mandatory)
After each checkpoint:
- Review design alignment with DESIGN.md.
- Evaluate if MVP scope is still minimal and extensible.
- Decide whether to proceed to the next phase.
