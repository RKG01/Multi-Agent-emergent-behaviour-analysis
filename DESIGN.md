# Emergent Behavior in Multi-Agent Systems for Insurance Fraud Detection
Document date: 2026-05-15
Version: 0.1 (design blueprint)

## 1. Project Overview
This system analyzes insurance claims for potential fraud using a coordinated set of AI agents. A FastAPI backend orchestrates multiple specialized agents (via LangGraph), each evaluating different signals such as claim validity, document consistency, behavioral patterns, and anomalies. A Streamlit frontend provides claim intake, live monitoring of agent activity, and dashboards for fraud risk and emergent behavior analytics. SQLite is used initially for easy, local data storage and logging.

Why multi-agent systems are useful:
- Specialized agents can focus on different evidence types, reducing blind spots.
- Parallel analysis improves throughput and yields richer evidence sets.
- Cross-agent disagreement is measurable and can be used as a signal for uncertainty.

What emergent behavior means here:
Emergent behavior is the appearance of system-level patterns or outcomes that arise from local interactions among agents, rather than being explicitly programmed into any single agent. In this system, emergence can show up as coordination without direct instruction, or as adverse dynamics like cascading errors.

Positive vs negative emergence:
- Positive emergence: stable consensus, complementary evidence, efficient convergence.
- Negative emergence: groupthink, feedback loops, redundant processing, or conflict spirals.

Research goals:
- Measure how agent interactions influence accuracy and consistency.
- Identify conditions that produce beneficial coordination.
- Detect and mitigate harmful emergent dynamics.

Expected outputs:
- Per-claim fraud risk score and decision rationale.
- Agent-level structured reports with evidence and confidence.
- Emergence analytics (coordination, conflict, redundancy metrics).
- Auditable logs and traces for research and reproducibility.

## 2. Problem Statement
Insurance fraud causes significant financial loss and often involves subtle, multi-factor signals across documents, timelines, and claimant behavior. A single model can miss cross-cutting patterns or overfit to limited signals. A decentralized, multi-agent approach allows independent evaluations that can surface contradictions, confirm evidence, and reveal emergent behavior that improves or degrades the overall decision quality.

## 3. Research Objectives
- Fraud detection: produce high-quality risk assessments and rationales.
- Emergent coordination: measure whether agents converge constructively.
- Conflict analysis: identify and interpret disagreements.
- Redundancy analysis: quantify duplicated reasoning and its impact.
- Performance evaluation: measure latency, accuracy, stability, and robustness.

## 4. System Architecture
### Components
- Streamlit frontend: claim intake, monitoring, dashboards.
- FastAPI backend: API gateway, orchestration entry point.
- LangGraph orchestration: agent graph, state management, routing.
- Gemini reasoning layer: LLM-based reasoning for each agent.
- SQLite database: claim storage, logs, emergence events, metrics.

### Request Flow
1. User uploads claim data and documents in Streamlit.
2. Streamlit calls FastAPI POST /analyze-claim.
3. FastAPI normalizes inputs and creates a FraudState.
4. LangGraph runs agent nodes and coordination steps.
5. Results and logs are written to SQLite.
6. FastAPI returns structured analysis to Streamlit.

### Component Interaction
- Streamlit only talks to FastAPI.
- FastAPI invokes LangGraph with a fully validated request.
- LangGraph nodes call Gemini through a shared client wrapper.
- Logging is centralized in the backend and never done by the UI.

### Data Flow
- Input data -> normalization -> persistence -> multi-agent analysis.
- Agent outputs -> conflict and redundancy analysis -> final decision.
- Logs and metrics -> SQLite -> dashboards.

### Agent Communication Flow
- Agents do not directly message each other.
- Coordinator Agent interprets and combines agent reports.
- Conflict Analyzer and Redundancy Analyzer use all agent outputs.

### Architecture Diagrams (ASCII)
High-Level Architecture:

+------------------+     +-----------+     +--------------------+
| User / Researcher| --> | Streamlit | --> | FastAPI API Gateway |
+------------------+     +-----------+     +--------------------+
                                                |
                                                v
                                         +---------------+
                                         | LangGraph     |
                                         | Orchestrator  |
                                         +---------------+
                                          /   |   |   \
                                         v    v   v    v
                                  +---------+ +---------+ +---------+ +---------+
                                  | Claim   | | Document| | Behavior| | Anomaly |
                                  | Validator| | Verifier| | Analyzer| | Detector|
                                  +---------+ +---------+ +---------+ +---------+
                                          \     |     /        /
                                           \    |    /        /
                                            v   v   v        v
                                          +--------------------+
                                          | Coordinator Agent  |
                                          +--------------------+
                                                  |
                                                  v
                                            +-----------+
                                            | SQLite DB |
                                            +-----------+
                                                  |
                                                  v
                                            +-----------+
                                            | API Reply |
                                            +-----------+

Request and Data Flow:

[Streamlit Upload] -> [FastAPI Validate] -> [LangGraph Run]
      |                       |                    |
      v                       v                    v
[SQLite claims]        [FraudState init]     [Agent reports]
      |                       |                    |
      v                       v                    v
[Logs + metrics] <----- [Coordinator + Emergence] <-+
      |
      v
[Streamlit dashboards]

Agent Communication Flow:

[Agent Reports] -> [Conflict Analyzer] -> [Coordinator] -> [Final Decision]
[Agent Reports] -> [Redundancy Analyzer] -> [Coordinator] -> [Final Decision]

## 5. Multi-Agent Design
All agents must return structured JSON. Each agent uses the same envelope:

AgentReport schema (common fields):
- agent_name: string
- decision_label: "low" | "medium" | "high"
- fraud_risk: float (0.0 to 1.0)
- confidence: float (0.0 to 1.0)
- evidence: list of {id, type, summary, source_ref}
- flags: list of strings
- uncertainties: list of strings
- errors: optional {code, message}

### 5.1 Claim Validator Agent
Responsibilities:
- Validate internal consistency of claim details (amounts, dates, policy rules).
- Detect missing or contradictory claim fields.

Inputs:
- Claim payload (policy, claimant, incident, amounts).
- Normalized rules (coverage limits, deductibles).

Outputs:
- AgentReport with validation findings and inconsistencies.

Prompt (template):
System: "You are a claim validation specialist. Identify internal inconsistencies and policy violations. Output JSON only."
User: "Claim: {claim_json} PolicyRules: {policy_rules} Output schema: {AgentReport schema}"

Validation logic:
- JSON schema check.
- fraud_risk and confidence in [0,1].
- evidence items must reference a source field or document id.

Failure cases:
- Missing or invalid claim fields.
- Response not in JSON format.

Interaction patterns:
- Runs early to detect structural issues.
- Output influences Coordinator weighting.

### 5.2 Document Verification Agent
Responsibilities:
- Check documents for consistency with claim details.
- Identify mismatched metadata, altered values, or missing docs.

Inputs:
- Document metadata and extracted text.
- Claim incident details.

Outputs:
- AgentReport with document inconsistencies.

Prompt (template):
System: "You verify documents against a claim. Output JSON only."
User: "Claim: {claim_json} Documents: {docs_json} Output schema: {AgentReport schema}"

Validation logic:
- Evidence references must include document ids.

Failure cases:
- Missing documents or unreadable text.

Interaction patterns:
- Runs after claim validation if documents exist.
- Triggers a missing-doc flag if required docs absent.

### 5.3 Behavioral Analysis Agent
Responsibilities:
- Evaluate claimant behavior for suspicious patterns (timing, prior history, anomalies).

Inputs:
- Claim history, claimant history, timeline features.

Outputs:
- AgentReport with behavioral risk features.

Prompt (template):
System: "You analyze claimant behavior patterns for fraud signals. Output JSON only."
User: "ClaimHistory: {history_json} CurrentClaim: {claim_json} Output schema: {AgentReport schema}"

Validation logic:
- Ensure uncertainties list is present if evidence is weak.

Failure cases:
- Insufficient historical data.

Interaction patterns:
- Runs in parallel with Document Verification.

### 5.4 Anomaly Detection Agent
Responsibilities:
- Identify outliers and unusual patterns in claim amounts, timing, and category distributions.

Inputs:
- Normalized numeric features and baselines.

Outputs:
- AgentReport with anomaly-based risk indicators.

Prompt (template):
System: "You detect anomalies in claim features. Output JSON only."
User: "Features: {features_json} Baselines: {baseline_json} Output schema: {AgentReport schema}"

Validation logic:
- fraud_risk must correlate with anomaly strength (simple heuristic check).

Failure cases:
- Missing baselines or malformed features.

Interaction patterns:
- Runs in parallel with Behavioral Analysis.

### 5.5 Coordinator Agent
Responsibilities:
- Aggregate all agent reports.
- Resolve conflicts using explicit rules.
- Produce final decision and rationale.

Inputs:
- All AgentReports.
- Conflict and redundancy summaries.

Outputs:
- FinalDecision schema:
  - final_label: "low" | "medium" | "high"
  - final_score: float (0.0 to 1.0)
  - rationale: list of evidence summaries
  - dissenting_views: list of agent_name

Prompt (template):
System: "You are the coordinator. Combine agent reports, identify conflicts, and produce a final decision. Output JSON only."
User: "Reports: {reports_json} Conflicts: {conflicts_json} Redundancy: {redundancy_json} Output schema: {FinalDecision schema}"

Validation logic:
- final_score in [0,1].
- If conflicts exist, dissenting_views must be non-empty.

Failure cases:
- Conflicting reports without a rationale.

Interaction patterns:
- Runs after all agent nodes complete.
- Produces final output returned to API caller.

## 6. LangGraph Workflow Design
### State Management
- LangGraph maintains a single FraudState object.
- Each node reads from the shared state and writes a structured update.
- State changes are append-only for logs and trace events.

### Nodes
1. ingest_request
2. claim_validator
3. document_verifier
4. behavioral_analyzer
5. anomaly_detector
6. conflict_analyzer
7. redundancy_analyzer
8. coordinator
9. finalize_and_log

### Edges and Conditional Routing
- ingest_request -> claim_validator
- claim_validator -> document_verifier (if documents present)
- claim_validator -> behavioral_analyzer (always)
- claim_validator -> anomaly_detector (always)
- document_verifier -> conflict_analyzer
- behavioral_analyzer -> conflict_analyzer
- anomaly_detector -> conflict_analyzer
- conflict_analyzer -> redundancy_analyzer
- redundancy_analyzer -> coordinator
- coordinator -> finalize_and_log

Conditional routing:
- If required documents are missing, document_verifier returns a missing-doc flag and continues.
- If conflict count exceeds a threshold, coordinator can request a single re-evaluation of the most uncertain agent.
- Loop prevention: each agent has a max_retries counter; coordinator cannot re-run more than once.

### Shared Memory and State Updates
- All agent outputs are stored in FraudState.agent_reports.
- Conflict and redundancy summaries are stored in FraudState.analysis.
- The final decision is stored in FraudState.final_decision.

### FraudState Schema (Pydantic-style)
FraudState:
- request_id: string
- claim_id: string
- received_at: datetime
- claim: ClaimInput
- documents: list[DocumentInput]
- features: FeatureSet
- agent_reports: dict[str, AgentReport]
- conflicts: list[ConflictRecord]
- redundancy: RedundancySummary
- emergence: EmergenceSummary
- final_decision: FinalDecision
- metrics: MetricsSnapshot
- trace: list[TraceEvent]
- retry_counters: dict[str, int]

ConflictRecord:
- pair: [agent_name_a, agent_name_b]
- field: string
- severity: "low" | "medium" | "high"
- description: string

RedundancySummary:
- overlap_score: float
- duplicated_evidence: list[EvidenceRef]

EmergenceSummary:
- coordination_score: float
- conflict_rate: float
- redundancy_score: float
- loop_risk: float

MetricsSnapshot:
- latency_ms: int
- token_usage: dict[str, int]
- model_calls: int

TraceEvent:
- ts: datetime
- node: string
- event: string
- details: object

## 7. Emergent Behavior Framework (Most Important)
### Definitions
- Positive emergence: system-level coordination that improves decision quality without explicit centralized control.
- Negative emergence: system-level dynamics that degrade decision quality or stability.

### Coordination Patterns (Positive)
- Independent convergence: agents agree using different evidence.
- Complementary coverage: each agent contributes unique, non-overlapping evidence.
- Stable consensus: minimal conflict across multiple claims of similar type.

### Conflict Patterns (Negative)
- Cascade disagreement: one agent disagreement increases others.
- Groupthink: multiple agents mirror a single weak signal.
- Feedback loop: coordinator repeatedly re-queries agents without new evidence.

### Redundant Processing
- Evidence duplication: agents cite identical sources repeatedly.
- Redundant logic: similar reasoning paths across agents.

### Feedback Loops and Prevention
- Limit each agent to one retry.
- Track repeated prompts by hash.
- Abort loop if output variance does not improve.

### Emergence Detection and Logging
The system detects emergence by comparing agent outputs over time and across claims. Each run generates an EmergenceSummary and optionally an emergence event.

Measurable metrics:
- coordination_score = 1 - normalized disagreement across agent labels
- conflict_rate = conflict_count / max(1, agent_pair_count)
- redundancy_score = average Jaccard overlap across evidence sets
- loop_risk = repeated_prompt_count / total_prompt_count
- dissent_ratio = dissenting_agents / total_agents

Emergence events are logged when:
- coordination_score crosses a positive threshold.
- conflict_rate or redundancy_score exceeds negative thresholds.
- loop_risk exceeds the safety limit.

## 8. Logging and Monitoring System
### Log Types
- Interaction logs: each node execution.
- Timestamps: start/end per node.
- Execution tracing: node transitions and retries.
- Conflict logs: field-level disagreements.
- Performance metrics: latency, tokens, model calls.
- Audit logs: final decisions and evidence references.

### Database Schemas (Log Tables)
agent_logs:
- id, request_id, agent_name, ts_start, ts_end, status, latency_ms,
  input_hash, output_json, errors

trace_events:
- id, request_id, ts, node, event, details_json

conflict_logs:
- id, request_id, agent_a, agent_b, field, severity, description

metrics:
- id, request_id, coordination_score, conflict_rate, redundancy_score,
  loop_risk, latency_ms, model_calls, token_usage_json

## 9. API Design (FastAPI)
### POST /analyze-claim
Request schema (JSON):
- claim_id: string
- claimant: object
- policy: object
- incident: object
- amount: number
- documents: list of {document_id, filename, text, metadata}

Response schema (JSON):
- request_id: string
- claim_id: string
- final_label: "low" | "medium" | "high"
- final_score: float
- agent_reports: object
- emergence: EmergenceSummary
- metrics: MetricsSnapshot

Example request:
{
  "claim_id": "C-123",
  "claimant": {"name": "A. Smith", "history_count": 2},
  "policy": {"policy_id": "P-9", "coverage_limit": 10000},
  "incident": {"date": "2026-05-01", "type": "collision"},
  "amount": 5200.75,
  "documents": [
    {"document_id": "D-1", "filename": "report.pdf", "text": "...", "metadata": {"source": "police"}}
  ]
}

Example response:
{
  "request_id": "R-789",
  "claim_id": "C-123",
  "final_label": "high",
  "final_score": 0.82,
  "agent_reports": {"ClaimValidator": {"decision_label": "medium", "fraud_risk": 0.6, "confidence": 0.7}},
  "emergence": {"coordination_score": 0.74, "conflict_rate": 0.2, "redundancy_score": 0.15, "loop_risk": 0.0},
  "metrics": {"latency_ms": 1240, "model_calls": 5}
}

### GET /logs
Query params:
- request_id (optional)
- agent_name (optional)
- limit (default 100)

Response:
- list of agent_logs

### GET /metrics
Query params:
- request_id (optional)
- limit (default 100)

Response:
- list of metrics rows

### GET /health
Response:
- status: "ok"
- timestamp: string

## 10. Frontend Design (Streamlit)
### Pages
1. Upload Page
- File uploader for claim documents.
- JSON form for claim data.
- Submit button to call /analyze-claim.

2. Live Agent Monitoring
- Timeline view of agent execution.
- Table of agent reports with confidence and risk.

3. Fraud Dashboard
- Per-claim risk score trends.
- Distribution of labels across claims.

4. Emergence Analytics Dashboard
- Coordination, conflict, redundancy charts.
- Emergence events log with filters.

5. Final Decision Page
- Final label, rationale, dissenting views.
- Evidence list with source references.

### UI Flow
Upload -> Analyze -> Live Monitoring -> Decision -> Dashboards.

## 11. Database Design (SQLite)
claims:
- id (pk), claim_id, received_at, claim_json, status

agent_logs:
- id (pk), request_id, agent_name, ts_start, ts_end, status,
  latency_ms, input_hash, output_json, errors

emergence_events:
- id (pk), request_id, ts, event_type, severity, details_json

metrics:
- id (pk), request_id, coordination_score, conflict_rate,
  redundancy_score, loop_risk, latency_ms, model_calls, token_usage_json

## 12. Gemini API Integration
- Gemini is used in each agent node for reasoning and summarization.
- The Coordinator Agent uses Gemini to synthesize and resolve conflicts.

Prompt engineering strategy:
- Strong system prompts with role constraints.
- Explicit JSON schema with strict output requirements.
- Deterministic temperature for consistency.

Structured outputs:
- Enforce JSON-only responses.
- Validate with Pydantic models.

Retry handling:
- Retry on invalid JSON or missing fields.
- Exponential backoff with max 2 retries.

Hallucination prevention:
- Require evidence references for each flag.
- Use uncertainty fields when evidence is weak.

## 13. Project Folder Structure (Proposed)
root/
  backend/
    app/
      main.py
      api/
      agents/
      orchestration/
      schemas/
      services/
      db/
      logging/
      core/
      utils/
    tests/
  frontend/
    app.py
    pages/
    components/
  docs/
    DESIGN.md
    IMPLEMENT.md
  scripts/
  data/

## 14. Development Roadmap
Phase 1: Setup and base infrastructure.
Phase 2: Single agent pipeline with one agent.
Phase 3: Multi-agent workflow.
Phase 4: Emergence tracking and analytics.
Phase 5: Streamlit dashboards and UI polish.
Phase 6: Evaluation and testing.

## 15. Evaluation Metrics
- Fraud detection accuracy
- Precision and recall
- Average latency per claim
- Conflict rate
- Redundancy score
- Coordination score
- Dissent ratio

## 16. Testing Strategy
- Unit tests for schemas and validation.
- Integration tests for LangGraph nodes.
- Agent tests with fixed fixtures.
- Workflow tests for routing and retries.
- Edge case tests for missing documents and conflicting evidence.

## 17. Future Improvements
- Redis or Postgres for scalable storage.
- Vector database for semantic document retrieval.
- Neo4j graph for fraud ring detection.
- Human-in-the-loop review workflows.
- Real-time streaming ingestion.
- Reinforcement learning for agent policy updates.

## 18. Coding Standards
- Modular architecture with clear boundaries.
- Use typing and Pydantic models everywhere.
- Prefer async FastAPI routes.
- Keep agents independent with structured outputs.
- Centralize logging and configuration.
- Use environment variables for secrets.
- Keep the MVP simple and extensible.
