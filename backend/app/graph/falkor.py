"""FalkorDB implementation of the TraceMind graph contract.

Only fixed relationship labels and query templates are used; browser/API input is
always supplied as a query parameter, never interpolated into Cypher.
"""
from __future__ import annotations
from datetime import datetime, timezone
import os
from urllib.parse import urlparse
from falkordb import FalkorDB

class FalkorGraph:
    def __init__(self, url: str | None = None, graph_name: str = "tracemind"):
        parsed = urlparse(url or os.getenv("FALKORDB_URL", "redis://localhost:6379"))
        self.db = FalkorDB(host=parsed.hostname or "localhost", port=parsed.port or 6379)
        self.graph = self.db.select_graph(graph_name)

    def _query(self, statement, params=None):
        return self.graph.query(statement, params or {})

    @staticmethod
    def _rows(result):
        return getattr(result, "result_set", result)

    def healthy(self):
        self._query("RETURN 1")
        return True

    def count(self):
        rows = self._rows(self._query("MATCH (n) RETURN count(n)"))
        return int(rows[0][0]) if rows else 0

    def add_node(self, id, type, **props):
        if not type.replace("_", "").isalnum(): raise ValueError("Invalid graph label")
        self._query(f"MERGE (n:`{type}` {{id:$id}}) SET n += $props", {"id": id, "props": {"id": id, "type": type, **props}})

    def edge(self, source, rel, target, **props):
        if not rel.replace("_", "").isalnum(): raise ValueError("Invalid relationship")
        self._query(f"MATCH (a {{id:$source}}), (b {{id:$target}}) MERGE (a)-[r:`{rel}`]->(b) SET r += $props", {"source": source, "target": target, "props": props})

    def node(self, id):
        rows = self._rows(self._query("MATCH (n {id:$id}) RETURN labels(n), properties(n)", {"id":id}))
        if not rows: return None
        labels, props = rows[0]
        return {"id": props["id"], "type": props.get("type", labels[0]), **props}

    def get_nodes(self, ids):
        rows = self._rows(self._query("MATCH (n) WHERE n.id IN $ids RETURN labels(n), properties(n)", {"ids":ids}))
        return [{"id": p["id"], "type":p.get("type", labels[0]), **p} for labels,p in rows]

    def neighborhood(self, node_id):
        rows=self._rows(self._query("MATCH (n {id:$id})-[r]-(m) RETURN labels(n),properties(n),type(r),properties(r),labels(m),properties(m)",{"id":node_id}))
        nodes={}; edges=[]
        for nl,np,rel,rp,ml,mp in rows:
            nodes[np['id']]={"id":np['id'],"type":np.get('type',nl[0]),**np}; nodes[mp['id']]={"id":mp['id'],"type":mp.get('type',ml[0]),**mp}
            edges.append({"source":np['id'],"target":mp['id'],"label":rel,**rp})
        return {"nodes":list(nodes.values()),"edges":edges}

    def seed(self):
        if self.node("TRACEMIND-SEED-v2"): return False
        records=[
        ("checkout-service","Service","checkout-service",{"criticality":"tier-1"}),("payment-service","Service","payment-service",{}),("payment-api","Service","payment-api",{}),("order-service","Service","order-service",{}),("catalog-service","Service","catalog-service",{}),("auth-service","Service","auth-service",{}),
        ("team-payments","Team","Payments Platform",{}),("team-commerce","Team","Commerce",{}),("team-platform","Team","Platform",{}),("priya","Person","Priya Shah",{"role":"Payments SRE"}),("marco","Person","Marco Ruiz",{"role":"Commerce Engineer"}),("lena","Person","Lena Chen",{"role":"Platform Lead"}),("aisha","Person","Aisha Khan",{"role":"Incident Commander"}),
        ("DEP-184","Deployment","DEP-184",{"timestamp":"2026-10-18T08:42:00Z","environment":"production"}),("a91f2","Commit","a91f2",{"message":"reduce checkout client timeout"}),("PAY-432","Ticket","PAY-432",{"title":"Align payment gateway timeout"}),("DEC-91","Decision","DEC-91",{"title":"Use 2 second gateway timeout"}),("INC-104","Incident","INC-104",{"severity":"SEV-1","status":"open","timestamp":"2026-10-18T09:12:00Z","description":"Checkout failures increased after production deployment."}),("INC-071","Incident","INC-071",{"severity":"SEV-2","status":"resolved","timestamp":"2026-08-04T10:00:00Z","description":"Payment API timeouts during checkout."}),("RES-17","Resolution","RES-17",{"description":"Restore payment timeout to 5 seconds","result":"successful","confidence":0.94}),("repo-checkout","Repository","checkout-web",{}),("doc-timeouts","Document","Payment timeout runbook",{})]
        for i in range(8): records.append((f"INC-{88+i}","Incident",f"INC-{88+i}",{"severity":"SEV-3","status":"resolved"}))
        for id,t,name,props in records: self.add_node(id,t,name=name,**props)
        for a,r,b,p in [("INC-104","AFFECTS","checkout-service",{}),("checkout-service","DEPENDS_ON","payment-service",{}),("payment-service","DEPENDS_ON","payment-api",{}),("INC-104","STARTED_AFTER","DEP-184",{}),("DEP-184","DEPLOYED_TO","checkout-service",{}),("DEP-184","CONTAINS","a91f2",{}),("a91f2","IMPLEMENTS","PAY-432",{}),("PAY-432","RESULTED_IN","DEC-91",{}),("DEC-91","CHANGED","payment-api",{"reason":"timeout changed from 5 seconds to 2 seconds"}),("INC-071","AFFECTS","payment-api",{}),("INC-071","RESOLVED_BY","RES-17",{}),("RES-17","APPLIED_TO","payment-api",{}),("checkout-service","OWNED_BY","team-commerce",{}),("payment-api","OWNED_BY","team-payments",{}),("priya","MEMBER_OF","team-payments",{}),("team-payments","MAINTAINS","payment-api",{}),("RES-17","SUPPORTED_BY","doc-timeouts",{})]: self.edge(a,r,b,**p)
        self.add_node("TRACEMIND-SEED-v2","Meta",name="seed marker",version="2")
        return True

    def evidence_for_incident(self, incident_id):
        # The path itself is the authoritative retrieval primitive used by agents.
        query="""MATCH p=(i:Incident {id:$incident})-[:STARTED_AFTER]->(:Deployment)-[:CONTAINS]->(:Commit)-[:IMPLEMENTS]->(:Ticket)-[:RESULTED_IN]->(:Decision)-[:CHANGED]->(api:Service)
        MATCH (i)-[:AFFECTS]->(:Service)-[:DEPENDS_ON*1..2]->(api)
        MATCH (prior:Incident)-[:AFFECTS]->(api)<-[:APPLIED_TO]-(res:Resolution)<-[:RESOLVED_BY]-(prior)
        RETURN [n IN nodes(p) | n.id], [r IN relationships(p) | type(r)], prior.id, res.id"""
        rows=self._rows(self._query(query,{"incident":incident_id}))
        if not rows: return None
        ids, rels, prior,res=rows[0]
        return ids,rels,prior,res

    def create_memory(self, incident_id, tenant, description):
        stamp=datetime.now(timezone.utc).isoformat(); id=f"MEM-{tenant}-{int(datetime.now().timestamp()*1000)}"
        self.add_node(id,"Memory",name="resolution precedent",description=description,tenant_id=tenant,confidence=.94,created_at=stamp)
        self.edge(id,"DERIVED_FROM",incident_id,timestamp=stamp); self.edge(id,"REMEMBERS","RES-17",timestamp=stamp)
        return self.node(id)

    def memories(self, tenant):
        rows=self._rows(self._query("MATCH (m:Memory {tenant_id:$tenant}) RETURN labels(m),properties(m) ORDER BY m.created_at DESC",{"tenant":tenant}))
        return [{"id":p['id'],"type":p.get('type',labels[0]),**p} for labels,p in rows]

    def incidents(self):
        rows=self._rows(self._query("MATCH (i:Incident) RETURN labels(i),properties(i) ORDER BY i.id"))
        return [{"id":p["id"],"type":p.get("type",labels[0]),**p} for labels,p in rows]
