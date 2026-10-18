# Graph schema

```mermaid
graph LR
 Incident--AFFECTS-->Service--DEPENDS_ON-->Service
 Incident--STARTED_AFTER-->Deployment--CONTAINS-->Commit--IMPLEMENTS-->Ticket--RESULTED_IN-->Decision--CHANGED-->Service
 Incident--RESOLVED_BY-->Resolution--APPLIED_TO-->Service
 Team--MAINTAINS-->Service
 Memory--DERIVED_FROM-->Incident
```

Nodes include Incident, Service, Deployment, Commit, Ticket, Decision, Resolution, Team, Person, Investigation, Finding, AgentRun, Action and Memory. Edge metadata can include source, timestamp, confidence, reason and status.
