import os
from fastapi.testclient import TestClient
from backend.app.graph.store import GraphStore
from backend.app.agents.orchestrator import IncidentOrchestrator
from backend.app.main import app

def store(tmp_path):
    g=GraphStore(str(tmp_path/'graph.json')); g.seed(); return g
def test_seed_idempotent(tmp_path):
    g=store(tmp_path); before=len(g.nodes); assert g.seed() is False; assert len(g.nodes)==before
def test_multihop_evidence(tmp_path):
    r=IncidentOrchestrator(store(tmp_path)).investigate('INC-104','t1'); ids={n['id'] for n in r.evidence_paths[0].nodes}; assert {'DEP-184','a91f2','PAY-432','DEC-91'}.issubset(ids)
def test_persistent_memory_and_tenant_isolation(tmp_path):
    p=str(tmp_path/'persistent.json'); g=GraphStore(p);g.seed();g.create_memory('INC-104','one','safe'); assert len(GraphStore(p).memories('one'))==1; assert not GraphStore(p).memories('two')
def test_api_health_and_investigation():
    c=TestClient(app); assert c.get('/health').status_code==200; r=c.post('/api/investigations',json={'incident_id':'INC-104','tenant_id':'test'}); assert r.status_code==200; assert r.json()['evidence_paths']
def test_action_is_simulated():
    c=TestClient(app);r=c.post('/api/actions/ACT-1/approve',json={'approved_by':'Priya'});assert r.json()['executed'] is False
