"""Small deterministic graph repository. Cypher equivalents live beside traversals.

The graph contract is deliberately relationship-first, so replacing this demo store
with FalkorDBGraphRepository is a storage change rather than an agent rewrite.
"""
from __future__ import annotations
import json, os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

class GraphStore:
    def __init__(self, path: str | None = None):
        self.path = Path(path or os.getenv("TRACEMIND_STATE_FILE", "/tmp/tracemind-graph.json"))
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []
        self.load()

    def load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text())
            self.nodes, self.edges = data["nodes"], data["edges"]

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"nodes": self.nodes, "edges": self.edges}, indent=2))

    def add_node(self, id: str, type: str, **props):
        self.nodes[id] = {"id": id, "type": type, **props}

    def edge(self, source: str, rel: str, target: str, **props):
        entry = {"source": source, "label": rel, "target": target, **props}
        if entry not in self.edges: self.edges.append(entry)

    def related(self, node: str, labels: set[str] | None = None):
        return [e for e in self.edges if e["source"] == node and (not labels or e["label"] in labels)]

    def neighborhood(self, node: str):
        edges = [e for e in self.edges if e["source"] == node or e["target"] == node]
        ids = {node} | {e["source"] for e in edges} | {e["target"] for e in edges}
        return {"nodes": [self.nodes[x] for x in ids if x in self.nodes], "edges": edges}

    def seed(self):
        if self.nodes: return False
        # Seed modeled as explicit graph records; no conclusion is stored on INC-104.
        for id, typ, name, extra in [
          ("checkout-service","Service","checkout-service",{"criticality":"tier-1"}), ("payment-service","Service","payment-service",{}), ("payment-api","Service","payment-api",{}), ("order-service","Service","order-service",{}), ("catalog-service","Service","catalog-service",{}), ("auth-service","Service","auth-service",{}),
          ("team-payments","Team","Payments Platform",{}),("team-commerce","Team","Commerce",{}),("team-platform","Team","Platform",{}),
          ("priya","Person","Priya Shah",{"role":"Payments SRE"}),("marco","Person","Marco Ruiz",{"role":"Commerce Engineer"}),
          ("DEP-184","Deployment","DEP-184",{"timestamp":"2026-10-18T08:42:00Z","environment":"production"}), ("a91f2","Commit","a91f2",{"message":"reduce checkout client timeout"}), ("PAY-432","Ticket","PAY-432",{"title":"Align payment gateway timeout"}), ("DEC-91","Decision","DEC-91",{"title":"Use 2 second gateway timeout"}),
          ("INC-104","Incident","INC-104",{"severity":"SEV-1","status":"open","timestamp":"2026-10-18T09:12:00Z","description":"Checkout failures increased after production deployment."}),
          ("INC-071","Incident","INC-071",{"severity":"SEV-2","status":"resolved","timestamp":"2026-08-04T10:00:00Z","description":"Payment API timeouts during checkout."}), ("RES-17","Resolution","RES-17",{"description":"Restore payment timeout to 5 seconds","result":"successful","confidence":0.94}),
          ("repo-checkout","Repository","checkout-web",{}),("doc-timeouts","Document","Payment timeout runbook",{}),
        ]: self.add_node(id,typ,name=name,**extra)
        for n in ["INC-088","INC-092","INC-099","INC-101","INC-102","INC-103"]: self.add_node(n,"Incident",name=n,severity="SEV-3",status="resolved")
        for n in ["team-identity","team-observability"]: self.add_node(n,"Team",name=n)
        self.edge("INC-104","AFFECTS","checkout-service"); self.edge("checkout-service","DEPENDS_ON","payment-service"); self.edge("payment-service","DEPENDS_ON","payment-api")
        self.edge("INC-104","STARTED_AFTER","DEP-184"); self.edge("DEP-184","DEPLOYED_TO","checkout-service"); self.edge("DEP-184","CONTAINS","a91f2"); self.edge("a91f2","IMPLEMENTS","PAY-432"); self.edge("PAY-432","RESULTED_IN","DEC-91"); self.edge("DEC-91","CHANGED","payment-api", reason="timeout changed from 5 seconds to 2 seconds")
        self.edge("INC-071","AFFECTS","payment-api"); self.edge("INC-071","RESOLVED_BY","RES-17"); self.edge("RES-17","APPLIED_TO","payment-api"); self.edge("checkout-service","OWNS","team-commerce"); self.edge("payment-api","OWNS","team-payments"); self.edge("priya","MEMBER_OF","team-payments"); self.edge("team-payments","MAINTAINS","payment-api"); self.edge("RES-17","SUPPORTED_BY","doc-timeouts")
        self.save(); return True

    def create_memory(self, incident_id: str, tenant: str, description: str):
        id = f"MEM-{len([n for n in self.nodes if n.startswith('MEM-')])+1:03}"
        self.add_node(id,"Memory",name="resolution precedent",description=description,tenant_id=tenant,confidence=.94,created_at=datetime.now(timezone.utc).isoformat())
        self.edge(id,"DERIVED_FROM",incident_id); self.edge(id,"REMEMBERS","RES-17"); self.save(); return self.nodes[id]

    def memories(self, tenant: str):
        return [n for n in self.nodes.values() if n["type"] == "Memory" and n.get("tenant_id") == tenant]
