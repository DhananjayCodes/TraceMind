# Hackathon track mapping

| Track | Evidence |
|---|---|
| Agents That Act on Connected Data | `backend/app/agents/orchestrator.py` traces deployment → commit → ticket → decision and emits `EvidencePath`. |
| Agent Memory and Coordination | `GraphStore.create_memory`, tenant filtering, and commander activity state; `backend/tests/test_app.py` verifies persistence. |
| Company Brain | deterministic company context in `GraphStore.seed`, graph explorer, owner/dependency/decision/resolution relationships. |

The UI never exposes chain-of-thought: it shows only graph records and short factual rationale.
