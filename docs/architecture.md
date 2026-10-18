# Architecture

```mermaid
flowchart TD
 UI[React operations dashboard] --> API[FastAPI]
 API --> C[Incident Commander]
 C --> I[Investigator]
 C --> M[Memory Agent]
 C --> A[Action Agent]
 I & M & A --> G[(FalkorDB context graph)]
```

The commander persists investigation state. Investigator follows deployment/code relationships, Memory Agent follows precedent/resolution relationships, and Action Agent only proposes approval-gated simulations.
