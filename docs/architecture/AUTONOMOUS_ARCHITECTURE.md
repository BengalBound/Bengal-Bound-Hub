# Autonomous Platform Architecture
# Bengal Bound — "The Platform That Runs Itself"
# BengalBound Ltd | v1.0

---

## Vision: Zero-Human Infrastructure

```
Traditional SaaS: Engineers monitor → detect issues → fix manually → deploy
Bengal Bound:           Rex monitors → Inspector validates → Kai auto-fixes → deploys

Traditional SaaS: Client emails support → human reads → human responds
Bengal Bound:           Shield AI detects issue → Concierge auto-responds → Finn checks billing

Traditional SaaS: Human writes reports → sends to client → waits for response
Bengal Bound:           Reporting Bot generates → Iris emails → client approves in-app
```

---

## 1. Multi-Tenant Client Architecture

### Client Workspace Hierarchy
```
Bengal Bound (Super Admin)
      │
      ├── Client: Dhaka Agency Ltd (client_id: clt_001)
      │     ├── Owner: Rahman Ahmed (role: OWNER)
      │     ├── Manager: Sara Islam (role: MANAGER)
      │     ├── Analyst: Karim Hassan (role: ANALYST)
      │     └── AI Agents: Concierge, Serea, Lead Hunter
      │
      ├── Client: Dubai Consulting LLC (client_id: clt_002)
      │     ├── Owner: Ahmed Al-Rashid (role: OWNER)
      │     ├── Team Member: Maria Santos (role: MEMBER)
      │     └── AI Agents: Oracle, Iris, Reporting Bot
      │
      └── Client: Nairobi Clinic (client_id: clt_003)
            ├── Owner: Dr. Amina Osei (role: OWNER)
            └── AI Agents: MediBook, Concierge
```

### User Roles per Client Workspace
| Role | Permissions |
|---|---|
| **OWNER** | Full access, billing, invite/remove team, all agents |
| **MANAGER** | All agents, team management, no billing |
| **ANALYST** | View analytics, approve/reject, no config changes |
| **MEMBER** | View activity feed, receive notifications, no agent control |
| **API_KEY** | Programmatic access, scoped to specific agents |

### Client Dashboard (Each client sees their own world)
```
┌──────────────────────────────────────────────────────────────────┐
│  Dhaka Agency Ltd — Console              [+ Invite Team Member]  │
│  Owner: Rahman Ahmed                     [Upgrade Plan]          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  MY AI TEAM (3 Active Agents)                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ 🤖 Concierge │  │ 🤖 Serea    │  │ 🤖 Lead Hunt │             │
│  │ ● Active     │  │ ● Active    │  │ ● Active     │             │
│  │ 12 leads     │  │ 847 posts   │  │ 34 prospects │             │
│  │ today        │  │ reviewed    │  │ found        │             │
│  │ [Configure]  │  │ [Configure] │  │ [Configure]  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                   │
│  ⚠ NEEDS APPROVAL (2)           TEAM MEMBERS (3)                │
│  ─────────────────               ──────────────                  │
│  Concierge wants to book         • Rahman Ahmed (Owner)          │
│  a meeting with Tahmid Corp      • Sara Islam (Manager)          │
│  [Approve] [Reject] 4h left      • Karim Hassan (Analyst)        │
│                                  [+ Invite Member]               │
│  Lead Hunter found premium       ──────────────                  │
│  prospect — send cold email?     MY PLAN: Mid                    │
│  [Approve] [Reject] 20h left     3 agents / 5 users              │
│                                  [Upgrade to Senior]             │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Self-Healing Infrastructure

### The Autonomous Operations Stack

```
┌─────────────────────────────────────────────────────────────────┐
│              BengalBound HUB SELF-HEALING LAYER                  │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────────────────────┐   │
│  │  REX             │    │  KAI                             │   │
│  │  Cybersecurity   │    │  DevOps Engineer                  │   │
│  │  Agent           │    │  Agent                           │   │
│  │                  │    │                                  │   │
│  │  Monitors:       │    │  Can execute:                    │   │
│  │  • API endpoints │    │  • Gunicorn + Nginx on VPS redeploy│  │
│  │  • Auth attempts │    │  • Database migrations           │   │
│  │  • Anomaly score │    │  • Dependency updates            │   │
│  │  • SSL certs     │    │  • GitHub Actions triggers       │   │
│  │  • CVE feeds     │    │  • Scaling adjustments           │   │
│  │  • Error rates   │    │  • Cache clearing                │   │
│  └────────┬─────────┘    └──────────────┬───────────────────┘   │
│           │                              │                       │
│           └──────────────┬───────────────┘                       │
│                          │                                       │
│                   INSPECTOR GATE                                  │
│                   (validates every automated action)             │
│                          │                                       │
│                          ▼                                       │
│              ACTION EXECUTED AUTOMATICALLY                       │
│              (if approved by Inspector)                          │
│                          │                                       │
│              Notification → CTO + CEO                           │
│              "Kai auto-fixed: restarted crashed worker"          │
└─────────────────────────────────────────────────────────────────┘
```

### Self-Healing Scenarios (Automated, No Human Needed)

| Scenario | Detected By | Auto-Fix | Notification |
|---|---|---|---|
| API endpoint returns 500 errors | Rex (error rate monitor) | Kai restarts Gunicorn + Nginx on VPS service | CTO Slack alert |
| SSL cert expiring in 30 days | Rex (cert monitor) | Kai triggers cert renewal via Cloudflare API | CEO + CTO email |
| New CVE in dependency | Rex (Dependabot webhook) | Kai creates GitHub PR with update | CTO Slack |
| Database connections maxed | Rex (Cloud SQL metrics) | Kai scales up connection pool | CTO alert |
| LiteLLM proxy (LITELLM_BASE_URL) rate limit hit | Rex (API monitor) | Kai switches to Ollama fallback automatically | CTO alert |
| Inspector unavailable | Rex (health check) | Kai auto-restarts Inspector instance | CRITICAL: CEO + CTO paged |
| Disk usage > 80% | Rex (storage monitor) | Kai archives old logs to Cloud Storage | CTO alert |
| Failed build on main branch | Kai (CI monitor) | Kai reverts to last stable deploy | Dev team Slack |
| Unusual login patterns | Rex (auth monitor) | Rex auto-blocks IP via Cloudflare API | Security Slack |

---

## 3. AI Agent Orchestration Frameworks

### Framework Stack (Best-in-Class)

| Framework | Purpose | Why |
|---|---|---|
| **LangGraph** (by LangChain) | Multi-step agent reasoning, state machines | Complex agents that plan across multiple steps |
| **CrewAI** | Multi-agent collaboration (agents work as a team) | Reporting Bot + Nova + Finn collaborating on reports |
| **AutoGen** (Microsoft) | Agent-to-agent conversations | Agents that negotiate and verify each other |
| **Pydantic AI** | Type-safe AI output parsing | Validate every AI response before use |
| **Instructor** | Structured AI outputs (JSON from LLM) | Never get malformed AI responses |
| **LiteLLM** | AI provider abstraction (100+ LLMs) | One interface for LiteLLM proxy (LITELLM_BASE_URL), OpenAI, Ollama, Claude |
| **OpenClaw** | Cybersecurity monitoring (your own tool) | Feeds threat data directly to Rex agent |

### LiteLLM — The AI Provider Abstraction (Key Decision)
```python
# ONE interface. Switch AI provider with ONE env variable.
from litellm import completion

class AIEngine:
    """
    Switch from LiteLLM proxy to Ollama to Claude with:
    AI_PROVIDER=litellm        → uses LiteLLM proxy (LITELLM_BASE_URL)
    AI_PROVIDER=ollama/llama3  → uses local Ollama (zero cost)
    AI_PROVIDER=claude-3-haiku → uses Anthropic Claude
    AI_PROVIDER=gpt-4o-mini    → uses OpenAI
    """

    def generate(self, prompt: str, system: str = "") -> str:
        response = completion(
            model=settings.AI_MODEL,    # "litellm/gemini-1.5-flash"
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
```

### CrewAI — Multi-Agent Collaboration (Example: Monthly Report)
```python
from crewai import Agent, Task, Crew

class MonthlyReportCrew:
    """Multiple agents collaborate to produce the monthly business report"""

    def __init__(self, client_id: str):
        self.data_analyst = Agent(
            role="Nova — Data Scientist",
            goal="Analyse all metrics and identify trends",
            backstory="Expert in business analytics",
            tools=[DatabaseQueryTool(client_id=client_id)]
        )
        self.report_writer = Agent(
            role="Reporting Bot",
            goal="Write clear, actionable business reports",
            backstory="Expert business writer",
            tools=[PDFGeneratorTool()]
        )
        self.finance_reviewer = Agent(
            role="Finn — Financial Analyst",
            goal="Verify all financial figures are accurate",
            tools=[AccountingQueryTool(client_id=client_id)]
        )

    def run(self) -> str:
        # Inspector gates the final report before delivery
        crew = Crew(
            agents=[self.data_analyst, self.finance_reviewer,
                    self.report_writer],
            tasks=[...],
            verbose=True
        )
        return crew.kickoff()
```

### OpenClaw Integration with Rex
```python
# Rex uses OpenClaw for advanced threat detection
class RexCybersecurityAgent:
    """Rex + OpenClaw = military-grade security monitoring"""

    def __init__(self):
        self.openclaw = OpenClawClient(
            api_key=settings.OPENCLAW_API_KEY,
            endpoint=settings.OPENCLAW_HOST
        )

    def monitor_continuously(self):
        """Runs every 30 seconds — always watching"""
        threats = self.openclaw.get_threat_intelligence()
        anomalies = self.openclaw.scan_network_traffic()

        for threat in threats + anomalies:
            if threat.severity >= ThreatLevel.HIGH:
                # Inspector validates auto-response
                action = self.determine_response(threat)
                Inspector.evaluate_and_execute(action)
                self.alert_team(threat)
```

---

## 4. Vector Knowledge Base (Per Client)

Each client's knowledge base is stored as vector embeddings — agents use semantic search:

```python
# Using Qdrant (open-source, self-hostable vector DB)
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

class ClientKnowledgeBase:
    """Per-client vector store for AI agent context"""

    COLLECTION = "bengalbound_client_{client_id}_knowledge"

    def __init__(self, client_id: str):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.collection = self.COLLECTION.format(client_id=client_id)

    def add_document(self, text: str, metadata: dict):
        """Store new knowledge (FAQ, policy, product info)"""
        embedding = embed(text)  # LiteLLM proxy (LITELLM_BASE_URL) text-embedding
        self.client.upsert(collection_name=self.collection,
                          points=[PointStruct(vector=embedding,
                                             payload=metadata)])

    def search(self, query: str, limit: int = 5) -> list[str]:
        """Agent searches client's knowledge before responding"""
        embedding = embed(query)
        results = self.client.search(self.collection,
                                     query_vector=embedding,
                                     limit=limit)
        return [r.payload['text'] for r in results]
```

---

## 5. Performance Architecture

### Caching Strategy (Progressive)
```
Phase 0–1 (0–200 clients):   diskcache (no Redis needed, $0)
Phase 2 (200–2K clients):    Redis Cloud (managed, $29/month)
Phase 3 (2K–10K clients):    Redis Cluster (multi-node)

Cache layers:
  L1: In-process (Python lru_cache) — microseconds
  L2: Redis — milliseconds
  L3: PostgreSQL — 10–100ms
  L4: LiteLLM proxy (LITELLM_BASE_URL) call — 500ms–3s (only when cache misses)
```

### TimescaleDB for IoT & Analytics
```sql
-- IoT time-series data stored in TimescaleDB extension
CREATE TABLE agent_telemetry (
    time        TIMESTAMPTZ NOT NULL,
    client_id   UUID NOT NULL,
    agent_name  VARCHAR(50),
    metric      VARCHAR(100),
    value       DOUBLE PRECISION
);
SELECT create_hypertable('agent_telemetry', 'time');
-- Auto-partitioned by time. Queries on last 7 days = instant.
```

### Event-Driven Architecture (Phase 2+)
```
Agent completes task
      │
      ▼
Publishes event to message queue
      │
      ├── Notification service subscribes → sends alerts
      ├── Analytics service subscribes → updates dashboards
      ├── Billing service subscribes → logs usage
      └── Rex subscribes → checks for anomalies
```

---

## 6. Complete Technology Stack (Final)

| Layer | Technology | Why |
|---|---|---|
| **AI Orchestration** | LiteLLM + LangGraph + CrewAI | Best-in-class, swappable |
| **AI Models** | LiteLLM proxy (LITELLM_BASE_URL) (primary) | Cost-efficient, fast |
| **AI Fallback** | Ollama (llama3, mistral) | Zero cost, self-hosted |
| **Vector DB** | Qdrant (self-hosted Phase 1 → Cloud Phase 3) | Open-source, fast |
| **API** | Django 4.2 LTS + DRF + Ninja | Batteries-included + speed |
| **Task Queue** | APScheduler (Phase 0) → Celery + Redis (Phase 2) | Scale as needed |
| **Database** | PostgreSQL 16 + TimescaleDB | Time-series + relational |
| **Cache** | diskcache → Redis Cluster | Scale as needed |
| **Search** | PostgreSQL FTS → Elasticsearch (Phase 3) | Scale as needed |
| **Security** | OpenClaw + Inspector + Cloudflare | Multi-layer |
| **Console** | Django templates (DRF + Next.js in future roadmap) | Server-rendered, dev-ready |
| **Mobile/Desktop** | Web (Django templates) — mobile deferred | Web-first, pragmatic |
| **IoT** | EMQX Cloud + Paho MQTT | 100M+ device scale |
| **Hosting** | Gunicorn + Nginx on VPS (API) + Netlify (Web) | Fixed-cost, maintainable |
| **Monitoring** | Sentry + Datadog (Phase 2) + OpenClaw | Full observability |
| **CI/CD** | GitHub Actions | Automated, secure |

---

*BengalBound Ltd — Autonomous Architecture v1.0*
*"The platform runs itself. You run the business."*
