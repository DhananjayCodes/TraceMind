"""Deterministic, no-LLM TraceMind showcase."""
from backend.app.graph.store import GraphStore
from backend.app.agents.orchestrator import IncidentOrchestrator
g=GraphStore(); g.seed(); r=IncidentOrchestrator(g).investigate("INC-104","demo-tenant")
print("TraceMind demo: INC-104")
print(r.suspected_root_cause); print(r.recommended_action)
print("Evidence:", " -> ".join(n["id"] for n in r.evidence_paths[0].nodes))
print("Stored memory:", g.memories("demo-tenant"))
