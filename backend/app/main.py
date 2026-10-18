import os
if __name__ == "__main__" and __package__ is None:
    # Allow `python3 main.py` from backend/app during local development.
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.app.graph.store import GraphStore
from backend.app.graph.falkor import FalkorGraph
from backend.app.agents.orchestrator import IncidentOrchestrator
from backend.app.models.schemas import InvestigationRequest, ActionApproval

graph = FalkorGraph() if os.getenv("TRACEMIND_GRAPH_PROVIDER") == "falkor" else GraphStore()
graph.seed(); orchestrator=IncidentOrchestrator(graph); investigations={}
app=FastAPI(title="TraceMind", version="0.1.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173","http://localhost:3000"],allow_methods=["*"],allow_headers=["*"])
@app.get('/health')
def health(): return {"status":"ok","service":"tracemind","graph_nodes": graph.count() if hasattr(graph, "count") else len(graph.nodes)}
@app.get('/api/graph/health')
def graph_health(): return {"status":"ok","provider":"falkordb" if isinstance(graph, FalkorGraph) else "local-development-only","nodes": graph.count() if hasattr(graph, "count") else len(graph.nodes)}
@app.get('/api/incidents')
def incidents(): return graph.incidents() if hasattr(graph, 'incidents') else [n for n in graph.nodes.values() if n['type']=='Incident']
@app.get('/api/incidents/{incident_id}')
def incident(incident_id:str):
    if not (graph.node(incident_id) if hasattr(graph, 'node') else graph.nodes.get(incident_id)): raise HTTPException(404,'Incident not found')
    return {**(graph.node(incident_id) if hasattr(graph, "node") else graph.nodes[incident_id]),**graph.neighborhood(incident_id)}
@app.post('/api/investigations')
def investigate(payload:InvestigationRequest):
    try: result=orchestrator.investigate(payload.incident_id,payload.tenant_id)
    except KeyError: raise HTTPException(404,'Incident not found')
    investigations[result.id]=result; return result
@app.get('/api/investigations/{id}')
def investigation(id:str):
    if id not in investigations: raise HTTPException(404,'Investigation not found')
    return investigations[id]
@app.get('/api/graph/neighborhood/{node_id}')
def neighborhood(node_id:str):
    if not (graph.node(node_id) if hasattr(graph, 'node') else graph.nodes.get(node_id)): raise HTTPException(404,'Node not found')
    return graph.neighborhood(node_id)
@app.get('/api/agents/activity')
def agents(): return [{"name":"Incident Commander","role":"coordinates shared state"},{"name":"Investigator","role":"traverses deployment and code graph"},{"name":"Memory Agent","role":"retrieves graph precedents"},{"name":"Action Agent","role":"proposes approval-gated action"}]
@app.get('/api/memories')
def memories(tenant_id:str='acme'): return graph.memories(tenant_id)
@app.post('/api/actions/{action_id}/approve')
def approve(action_id:str,payload:ActionApproval): return {"id":action_id,"status":"approved_simulation","approved_by":payload.approved_by,"executed":False}
@app.post('/api/demo/reset')
def reset():
    if isinstance(graph, FalkorGraph): raise HTTPException(409, "Reset is only available in local development mode")
    graph.nodes={}; graph.edges=[]; graph.seed(); investigations.clear(); return {"status":"reset"}

@app.get("/")
def root():
    return {"service": "TraceMind API", "docs": "/docs", "health": "/health", "frontend": "http://localhost:5173"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
