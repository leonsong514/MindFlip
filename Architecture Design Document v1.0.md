# Architecture Design Document v1.0

**Status:** Architecture Baseline
**Target:** Windows Desktop MVP
**Project Type:** Local-first AI Decision Agent
**Primary Role:** AI Agent + Full-stack portfolio project

------

## 1. Product Definition

The application is a **local-first, model-agnostic AI decision-support system**.

Its purpose is not to replace human decision-making, but to help users:

- structure a decision;
- collect and evaluate evidence;
- compare alternatives;
- use analytical tools;
- record why a decision was made;
- record whether the user actually followed the decision;
- record the real-world outcome;
- review long-term decision patterns.

Core principle:

> **AI advises. Human decides. History remembers.**

The application is **not primarily a chatbot**.

The primary UI is a customizable decision dashboard. Conversational AI is one interaction method inside the product rather than the product itself.

------

# 2. Product Loop

The fundamental domain loop is:

```text
Context
   ↓
Think
   ↓
Analyze
   ↓
Compare
   ↓
Decide
   ↓
Record
   ↓
Follow / Ignore
   ↓
Outcome
   ↓
Review
   ↓
Long-term Insights
```

A critical product distinction is that the system records three separate concepts:

```text
AI Recommendation
        ↓
User Decision
        ↓
Actual Behaviour
        ↓
Real Outcome
```

They must never be collapsed into one field.

This allows future analysis such as:

```text
How frequently do I follow my original decisions?

When I ignore a decision, what happens?

Which decision criteria actually correlate with good outcomes?

Do I repeatedly underestimate certain risks?

How has my decision style changed over time?
```

------

# 3. Architecture Principles

The architecture follows eight rules.

### 3.1 Local First

User decisions, history, configuration and files are stored locally by default.

Cloud accounts and synchronization are future capabilities, not MVP requirements.

### 3.2 Model Agnostic

The Agent Core must never depend directly on one model provider.

```text
Agent Core
    ↓
Model Interface
    ↓
Provider Adapter
```

### 3.3 Dashboard First

The home screen is a decision intelligence dashboard.

Chat is secondary.

### 3.4 Structured Data Before RAG

Important decision information must exist as structured entities.

RAG is introduced later for semantic retrieval, not used as a substitute for proper data modeling.

### 3.5 Explicit Tool Boundaries

The LLM never directly executes arbitrary code or system commands.

Every capability passes through a registered tool interface and permission system.

### 3.6 Observable Agent Execution

The application exposes Agent activities such as:

```text
Search started
4 sources collected
File analyzed
Decision matrix calculated
Comparison generated
Recommendation produced
```

Private model reasoning is not treated as application state.

### 3.7 Async by Default

LLM streaming, cancellation, tools and Agent execution use an asynchronous architecture.

### 3.8 Mobile-Compatible Domain Layer

Desktop UI may depend on desktop capabilities.

Domain logic must not.

------

# 4. High-Level Architecture

```text
┌───────────────────────────────────────────────────────────┐
│                    Desktop Application                    │
│                                                           │
│  React + TypeScript                                       │
│                                                           │
│  Dashboard                                                │
│  Decision Workspace                                       │
│  Timeline                                                 │
│  Insights                                                 │
│  Model Settings                                           │
└───────────────────────────┬───────────────────────────────┘
                            │
                       Tauri IPC
                            │
┌───────────────────────────▼───────────────────────────────┐
│                     Tauri Host                            │
│                       Rust                                │
│                                                           │
│  Window management                                        │
│  Native permissions                                       │
│  Secure credential bridge                                 │
│  Python runtime lifecycle                                 │
│  File system boundary                                     │
└───────────────────────────┬───────────────────────────────┘
                            │
                     Local IPC / API
                            │
┌───────────────────────────▼───────────────────────────────┐
│                 Python Agent Runtime                      │
│                                                           │
│  Agent Engine                                             │
│  Model Gateway                                            │
│  Tool Registry                                            │
│  Decision Engine                                          │
│  Event System                                             │
│  File Analysis                                            │
│  Persistence                                              │
│  Evaluation                                               │
└─────────┬─────────────────┬───────────────────┬───────────┘
          │                 │                   │
          ▼                 ▼                   ▼
       SQLite            Models              Tools
                         APIs
```

------

# 5. Technology Stack

## Desktop

```text
Tauri 2
React
TypeScript
Vite
```

Tauri supports Windows, macOS, Linux, Android and iOS from the same broader ecosystem, while using the operating system WebView rather than bundling a full browser runtime. This fits the lightweight-desktop requirement and leaves a credible future mobile path.

For MVP:

```text
Official platform:
Windows

Architecture-ready:
macOS
Linux
Mobile
```

Windows installer generation is supported directly by Tauri's distribution tooling.

------

## Frontend

```text
React
TypeScript
Vite
TanStack Query
Zustand
React Router
```

Recommended UI foundation:

```text
Tailwind CSS
shadcn/ui primitives
Radix UI
Lucide icons
Framer Motion
```

Principle:

> UI libraries provide primitives, not visual identity.

The project should create its own:

```text
spacing system
typography
surface hierarchy
animation language
dashboard cards
decision visualizations
```

Do not visually resemble a default component-library demo.

------

# 6. UX Architecture

## Main Navigation

```text
Dashboard
Decisions
Timeline
Insights
Files
Tools
Settings
```

AI is available globally through:

```text
Command Palette
Context actions
Analysis button
Decision assistant
Inline suggestions
```

rather than forcing the user into a chat page.

------

# 7. Dashboard

Dashboard is the primary experience.

Example:

```text
┌──────────────────────────────────────────────────────────────┐
│ Good evening                                      ⌘ K       │
│                                                              │
│ Your Decision Pulse                                          │
│ ┌────────────────┐ ┌────────────────┐ ┌──────────────────┐ │
│ │ 12 Decisions   │ │ 72% Followed   │ │ 7 Reviewed       │ │
│ └────────────────┘ └────────────────┘ └──────────────────┘ │
│                                                              │
│ Recent Decisions                                             │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Laptop purchase                  Review in 16 days       │ │
│ │ Research direction               Outcome recorded       │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ AI Insight                                                   │
│ "You tend to assign high weight to short-term cost..."       │
│                                                              │
│ Decision Timeline          Outcome Patterns                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

Dashboard widgets should eventually be customizable.

------

# 8. Decision Workspace

A Decision is the main domain object.

```text
Decision
├── Goal
├── Context
├── Alternatives
├── Criteria
├── Evidence
├── Risks
├── Files
├── Agent Runs
├── Recommendation
├── User Decision
├── Follow-through
├── Outcome
└── Reviews
```

The workspace should support both:

### Lightweight Decision

```text
Random choice
Yes / No
Pros / Cons
Quick compare
```

and:

### Structured Decision

```text
Alternatives
Evidence
Criteria
Weights
Risk
Agent analysis
Decision matrix
Recommendation
Outcome review
```

------

# 9. Core Domain Model

Suggested conceptual schema:

```text
Workspace
    │
    └── Decision
         ├── Alternative[]
         ├── Criterion[]
         ├── Evidence[]
         ├── DecisionFile[]
         ├── AgentRun[]
         │    ├── AgentStep[]
         │    ├── ToolExecution[]
         │    └── ModelInteraction[]
         │
         ├── Recommendation[]
         ├── DecisionRevision[]
         ├── FollowThrough
         ├── Outcome[]
         └── Review[]
```

------

# 10. Important Entities

## Decision

```text
id
title
description
status
decision_type
created_at
decided_at
review_at
confidence
```

Possible statuses:

```text
draft
researching
evaluating
decided
observing
reviewed
archived
```

------

## Criterion

```text
id
decision_id
name
description
weight
```

------

## Alternative

```text
id
decision_id
name
description
status
```

------

## Evidence

```text
id
decision_id
source_type
source_uri
title
content_summary
collected_at
reliability_metadata
```

An Evidence object may originate from:

```text
web
file
user
calculation
agent
```

------

## Recommendation

AI recommendation must remain separate from the user's actual decision.

```text
recommendation_id
decision_id
agent_run_id
recommended_alternative
summary
confidence
created_at
```

------

## Decision Revision

```text
revision_id
decision_id
selected_alternative
reason
created_at
```

This preserves decision history instead of overwriting it.

------

# 11. Follow-Through Model

A first-class entity:

```text
FollowThrough

decision_id
followed_decision
actual_action
reason_for_deviation
recorded_at
```

Example:

```text
AI suggested: B

User decided: B

Actual behaviour: A

Reason:
"Time pressure changed the situation."
```

This distinction enables meaningful future behavioral analysis.

------

# 12. Outcome Model

```text
Outcome

decision_id
result
rating
notes
measured_at
```

Outcome must not automatically imply whether a decision was objectively good or bad.

User interpretation remains explicit.

------

# 13. Review Model

A future Decision Review may analyze:

```text
Original context
Original evidence
AI recommendation
User decision
Actual behaviour
Outcome
Changed assumptions
Lessons learned
```

Result:

```text
Decision Review
├── What happened?
├── Which assumptions held?
├── Which assumptions failed?
├── What changed?
└── What should be remembered?
```

------

# 14. Agent Architecture

The Agent is intentionally bounded.

```text
User Goal
   ↓
Context Builder
   ↓
Model
   ↓
Structured Action
   ↓
Tool / Analysis
   ↓
Observation
   ↓
Model
   ↓
...
   ↓
Recommendation
```

Default:

```text
max_steps = 8
```

No unlimited autonomous loop.

------

# 15. Agent Core

Proposed interface:

```python
class Agent:
    async def run(
        self,
        task: AgentTask,
        context: AgentContext,
        config: AgentConfig,
    ) -> AgentResult:
        ...
```

The Agent Core knows nothing about:

```text
OpenAI
Qwen
DeepSeek
Doubao
Ollama
```

It communicates only through `ModelProvider`.

------

# 16. Model Abstraction

```python
class ModelProvider:

    async def generate(...)
    async def stream(...)
    async def tool_call(...)

    def capabilities(...)
```

Provider implementations:

```text
OpenAIProvider
QwenProvider
DeepSeekProvider
DoubaoProvider
OllamaProvider
OpenAICompatibleProvider
```

LiteLLM can optionally be used behind this abstraction because it already provides unified access patterns, streaming and Ollama among many supported providers. However, the project should retain its own provider abstraction rather than exposing LiteLLM throughout the codebase.

------

# 17. Model Capability System

Every configured model receives capabilities:

```text
TEXT
STREAMING
TOOL_CALLING
STRUCTURED_OUTPUT
VISION
LONG_CONTEXT
```

Example:

```text
Qwen Model

Chat               ✓
Streaming          ✓
Tool Calling       ✓
Structured Output  ✓
Vision              —
```

Agent workflows declare requirements:

```text
DecisionResearchAgent

requires:
- TEXT
- TOOL_CALLING
```

Incompatible models generate a UI warning.

------

# 18. Model Configuration

Settings:

```text
Provider
Model
Base URL
API Key
Timeout
Temperature
Context Limit
```

Presets:

```text
OpenAI
Qwen
DeepSeek
Doubao
Ollama
Custom OpenAI-compatible
```

API credentials must not be stored as plaintext in SQLite.

Use the OS credential storage mechanism through the native layer.

------

# 19. Agent Tools

MVP Tool Registry:

```text
CalculatorTool
WebResearchTool
FileAnalysisTool
ComparisonTool
WeightedMatrixTool
PythonAnalysisTool
```

Later:

```text
MCPTool
PluginTool
SemanticSearchTool
```

------

# 20. Tool Interface

```python
class Tool:

    name: str
    description: str
    permission_level: PermissionLevel

    async def execute(
        self,
        arguments: dict,
        context: ToolContext
    ) -> ToolResult:
        ...
```

Tools return structured results.

Never return arbitrary undocumented strings when a typed object is possible.

------

# 21. Tool Permission Model

Three levels:

```text
SAFE
CONFIRM
RESTRICTED
```

Examples:

```text
Calculator
→ SAFE

Web request
→ SAFE / configurable

Read user-selected file
→ SAFE

Read arbitrary filesystem path
→ CONFIRM

Python analysis
→ CONFIRM

Shell
→ RESTRICTED / disabled
```

MVP provides **no unrestricted Shell tool**.

------

# 22. Python Analysis Sandbox

Python analysis exists for:

```text
statistics
CSV analysis
calculation
simple visualization
decision matrices
```

It must not behave as unrestricted operating-system access.

Initial implementation should enforce:

```text
temporary workspace
execution timeout
restricted working directory
limited file access
output size limit
process termination
```

Full container isolation can become a later security milestone.

------

# 23. Web Research

Web research is optional.

```text
Settings
Web Research

[ ] Enabled
```

The model and search mechanism are distinct concepts:

```text
LLM
≠
Search Engine
```

The architecture should therefore expose a:

```text
SearchProvider
```

interface independently from `ModelProvider`.

------

# 24. Evidence Architecture

Every meaningful researched claim can reference Evidence.

```text
Claim
   ↓
EvidenceReference[]
```

UI example:

```text
Battery life is approximately 15 hours [1]

[1] Manufacturer documentation
```

Evidence stores:

```text
source
retrieval date
title
source type
relevant excerpt metadata
```

This is essential to the product's `trustworthy` design goal.

------

# 25. Event Architecture

Agent execution produces domain events.

Example:

```text
AGENT_RUN_STARTED
MODEL_STREAM_STARTED
TOOL_REQUESTED
TOOL_APPROVAL_REQUIRED
TOOL_STARTED
TOOL_COMPLETED
EVIDENCE_ADDED
RECOMMENDATION_CREATED
AGENT_RUN_COMPLETED
AGENT_RUN_FAILED
```

Frontend subscribes to these events.

This powers:

```text
streaming
progress
activity timeline
cancellation
debugging
observability
```

------

# 26. Runtime State

Separate:

```text
Persistent State
```

from:

```text
Agent Runtime State
```

Runtime state includes:

```text
current step
messages
tool observations
token usage
current status
cancellation state
```

Do not persist internal temporary state unless required for recovery or audit.

------

# 27. Persistence Layer

MVP:

```text
SQLite
```

Recommended:

```text
SQLAlchemy 2
Alembic
```

Reasons:

```text
local-first
single-user
transactional
portable
mature
easy backup
easy migration
```

------

# 28. Retrieval

Phase 1:

```text
SQL queries
SQLite indexes
SQLite FTS
```

Phase 2:

```text
Embeddings
Semantic retrieval
RAG
```

RAG should primarily target:

```text
historical decisions
large document collections
semantic discovery
```

rather than replacing relational queries.

------

# 29. Local Storage Structure

Suggested:

```text
<AppData>/DecisionAgent/

database/
    app.db

files/
    decisions/
    imports/

cache/

logs/

exports/

runtime/
```

Never place credentials here in plaintext.

------

# 30. Frontend State

Separate:

```text
Server/runtime state
→ TanStack Query

Transient UI state
→ Zustand

Form state
→ React Hook Form
```

Avoid one giant global store.

------

# 31. IPC Boundary

Frontend must not call Python implementation details directly.

Preferred logical API:

```text
Frontend
   ↓
Application API
   ↓
Domain Services
   ↓
Agent / Database / Tools
```

Potential endpoints:

```text
decision.create
decision.get
decision.update

agent.run
agent.cancel

model.list
model.test

tool.list

file.import

insight.generate
```

This makes eventual migration to mobile/cloud APIs significantly easier.

------

# 32. Rust Layer

Rust must remain thin.

Responsibilities:

```text
Tauri application lifecycle
native dialogs
secure credential integration
filesystem permissions
Python runtime management
desktop IPC
OS integration
```

Not responsible for:

```text
Agent planning
decision logic
database business logic
model adapters
analysis
```

This avoids unnecessary Rust complexity.

------

# 33. Python Package Structure

```text
backend/
│
├── app/
│   ├── agent/
│   │   ├── engine.py
│   │   ├── state.py
│   │   └── events.py
│   │
│   ├── models/
│   │   ├── base.py
│   │   └── providers/
│   │
│   ├── tools/
│   │   ├── base.py
│   │   ├── registry.py
│   │   └── builtin/
│   │
│   ├── decisions/
│   │   ├── models.py
│   │   ├── service.py
│   │   └── schemas.py
│   │
│   ├── evidence/
│   ├── files/
│   ├── insights/
│   ├── persistence/
│   ├── security/
│   └── api/
│
└── tests/
```

------

# 34. Frontend Structure

```text
frontend/
│
├── src/
│   ├── app/
│   ├── routes/
│   ├── features/
│   │   ├── dashboard/
│   │   ├── decisions/
│   │   ├── insights/
│   │   ├── timeline/
│   │   ├── files/
│   │   └── settings/
│   │
│   ├── components/
│   ├── design-system/
│   ├── stores/
│   ├── api/
│   ├── hooks/
│   ├── types/
│   └── utils/
```

Prefer feature-based architecture over giant folders such as:

```text
components/
pages/
services/
```

with hundreds of unrelated files.

------

# 35. Plugin Architecture

Three extension points are planned:

```text
Tool Plugin
Model Provider
MCP
```

MVP formally exposes:

```text
Tool Plugin API
```

Internal tools use the same contract.

Future third-party tools therefore do not require Agent Core modification.

------

# 36. MCP

MCP support is an extension mechanism rather than the internal architecture.

```text
Agent
  ↓
Tool Registry
  ├── Built-in Tools
  ├── Plugin Tools
  └── MCP Adapter
         ↓
      MCP Servers
```

Do not require every built-in tool to run through MCP.

------

# 37. Decision Insights

Long-term analytics should initially use deterministic statistics.

Examples:

```text
decision count
follow-through rate
decision categories
average confidence
outcome ratings
decision duration
criterion usage
```

AI-generated interpretation sits above these metrics.

Architecture:

```text
Raw Decisions
     ↓
Deterministic Analytics
     ↓
Structured Metrics
     ↓
LLM Interpretation
```

Never ask the LLM to calculate statistics that the application can calculate deterministically.

------

# 38. Psychological / Behavioural Analysis Boundary

The system may identify patterns such as:

```text
"You frequently change decisions after time pressure is introduced."
```

It should not present itself as performing medical or psychological diagnosis.

The architecture should call this:

```text
Decision Behaviour Insights
```

rather than:

```text
Psychological Diagnosis
```

------

# 39. Reliability Strategy

For important analysis:

```text
source
↓
evidence
↓
analysis
↓
recommendation
```

The system should distinguish:

```text
Fact
User assumption
Model inference
Calculation
Recommendation
```

These are different data types conceptually and should remain distinguishable in the UI.

------

# 40. Failure Handling

An Agent Run may finish as:

```text
completed
cancelled
failed
partial
```

A failed tool must not automatically terminate the entire Agent.

Example:

```text
Web search failed
      ↓
Agent receives structured error
      ↓
May continue without web
      ↓
Clearly state evidence limitation
```

------

# 41. Observability

Development mode records:

```text
Agent Run ID
model
latency
tool calls
tool latency
token usage
exceptions
state transitions
```

Do not log:

```text
API keys
credential values
sensitive file contents
```

------

# 42. Testing Strategy

Four layers.

## Unit

```text
decision logic
tool parsing
model adapters
database
calculations
```

## Integration

```text
Agent + MockModel
Tool + Agent
Database + Services
Provider adapters
```

## Agent Evaluation

Fixed benchmark tasks:

```text
tool selection
argument correctness
multi-step execution
evidence usage
structured output
loop termination
```

Run against:

```text
MockModel
Reference cloud model
Optional local model
```

## Desktop E2E

```text
create decision
configure model
run analysis
approve tool
record decision
record outcome
review history
```

------

# 43. CI/CD

GitHub Actions:

```text
Pull Request
     ↓
Lint
     ↓
Type Check
     ↓
Unit Tests
     ↓
Integration Tests
     ↓
Frontend Build
     ↓
Backend Build
```

Release:

```text
Tag
 ↓
Build Windows
 ↓
Generate installer
 ↓
Checksum
 ↓
GitHub Release
```

Tauri provides official workflows/tooling around multi-platform binary builds, which can later support macOS/Linux expansion.

------

# 44. Security Model

Core principles:

```text
least privilege
explicit consent
local-first storage
credential isolation
bounded execution
auditable tools
```

Security boundaries:

```text
Frontend
   ↓
Tauri
   ↓
Agent Runtime
   ↓
Tool Permissions
   ↓
OS / Network / Files
```

No model output is considered trusted executable input.

------

# 45. Export / Portability

MVP:

```text
Markdown
JSON
```

Later:

```text
Workspace backup
Workspace restore
Encrypted backup
Cloud sync
```

User ownership of decision history is a product principle.

------

# 46. Future Cloud Architecture

Not implemented in MVP.

Potential later architecture:

```text
Desktop
   ↓
Sync Engine
   ↓
Cloud API
   ↓
User Account
   ↓
Encrypted Decision Data
```

Domain entities should therefore use stable UUIDs from the beginning.

------

# 47. Future Mobile Architecture

Desktop remains first priority.

Because Tauri 2 supports mobile targets as well as desktop targets, some application infrastructure can potentially be reused later, although platform-specific plugins can have different support levels.

Rule:

```text
Domain logic → portable
API contracts → portable
React concepts → reusable where practical
Desktop native capabilities → isolated
```

Do not compromise desktop UX today purely for hypothetical mobile reuse.

------

# 48. MVP Scope

## Must Have

```text
Windows desktop application

Dashboard

Decision CRUD

Lightweight decisions

Structured decisions

OpenAI
Qwen
DeepSeek
Doubao
Ollama

Agent Loop

Tool Registry

Calculator

Comparison

Weighted Matrix

File Analysis

Python Analysis

Optional Web Research

Evidence

Agent activity timeline

Decision revisions

Follow-through record

Outcome record

SQLite

Model settings

API credential security

JSON / Markdown export

Unit + integration testing

Windows build pipeline
```

------

# 49. Explicitly NOT MVP

```text
Cloud accounts

Cloud sync

macOS release

Mobile application

Full RAG

Vector database

Multi-agent architecture

Arbitrary Shell

Autonomous unlimited Agent

Team collaboration

Complex workflow editor

Plugin marketplace
```

Preventing these features from entering MVP is an architectural requirement.

------

# 50. Development Roadmap

## Phase 0 — Foundation

```text
Monorepo
Tauri
React
Python runtime
IPC
SQLite
CI
```

## Phase 1 — Decision Core

```text
Decision model
Alternatives
Criteria
Decision history
Dashboard
```

## Phase 2 — Model Layer

```text
ModelProvider
OpenAI-compatible adapter
Qwen
DeepSeek
Doubao
Ollama
Streaming
Capabilities
```

## Phase 3 — Agent

```text
Agent loop
Agent state
Events
Cancellation
Tool registry
Permissions
```

## Phase 4 — Analysis Tools

```text
Calculator
Comparison
Weighted Matrix
File analysis
Python analysis
Web research
```

## Phase 5 — Evidence

```text
Evidence entities
Claims
Sources
Activity timeline
```

## Phase 6 — Decision Lifecycle

```text
Recommendation
User decision
Revision
Follow-through
Outcome
Review
```

## Phase 7 — Insights

```text
Decision metrics
Timeline
Dashboard widgets
Behaviour insights
```

## Phase 8 — Production Quality

```text
E2E
Agent eval
Installer
Error recovery
Logging
Performance
Documentation
Plugin SDK
```

------

# 51. Repository Structure

```text
decision-agent/
│
├── apps/
│   ├── desktop/
│   └── backend/
│
├── packages/
│   ├── ui/
│   ├── contracts/
│   └── plugin-sdk/
│
├── docs/
│   ├── architecture/
│   │   ├── architecture-v1.md
│   │   └── adr/
│   ├── development/
│   └── plugin-development/
│
├── tests/
│   └── agent-evals/
│
├── scripts/
│
├── .github/
│   └── workflows/
│
├── LICENSE
├── CONTRIBUTING.md
└── README.md
```

------

# 52. Architecture Decision Records

Major decisions must receive ADRs.

Initial ADR set:

```text
ADR-001  Tauri over Electron

ADR-002  Python Agent Runtime

ADR-003  SQLite local persistence

ADR-004  Model Provider abstraction

ADR-005  Agent tools and permissions

ADR-006  Structured decision domain model

ADR-007  Event-driven Agent runtime

ADR-008  Local-first architecture

ADR-009  RAG deferred from MVP

ADR-010  Licensing strategy
```

------

# 53. Portfolio / Interview Coverage

The project should intentionally demonstrate:

### Frontend

```text
React
TypeScript
state management
design system
async UI
streaming
dashboard visualization
```

### Backend

```text
Python
asyncio
API design
domain modeling
SQLite
ORM
migration
validation
```

### Agent Engineering

```text
Agent loop
tool calling
model abstraction
structured output
memory/state
tool permission
Agent evaluation
MCP
```

### Desktop

```text
Tauri
IPC
native permissions
packaging
credential storage
```

### Software Engineering

```text
clean architecture
plugin architecture
testing
CI/CD
logging
security
versioning
ADR
```

The project should favor **architectural clarity over feature count**.

------

# 54. Project Success Criteria

The MVP succeeds when a user can:

```text
1. Install the Windows application.

2. Configure their preferred model.

3. Create a decision.

4. Add alternatives and criteria.

5. Ask AI to analyze it.

6. Observe the Agent using tools.

7. Inspect evidence.

8. Make their own final decision.

9. Later record whether they followed it.

10. Record the outcome.

11. Review the original reasoning.

12. See patterns across historical decisions.
```

If these twelve steps feel polished, fast and trustworthy, the project has achieved its core objective.

------

# 55. Architecture Summary

```text
                  React / TypeScript
                         │
                         │
                       Tauri
                         │
                         │
                 Python Agent Runtime
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       Agent          Decision        Tools
       Engine          Domain
          │              │              │
          │              │              │
      Model API        SQLite       Tool Registry
          │
    ┌─────┼─────┬────────┬─────────┐
    │     │     │        │         │
 OpenAI Qwen DeepSeek Doubao    Ollama
```

The central architectural rule is:

> **The Decision domain owns the product.
> The Agent assists the Decision domain.
> The model assists the Agent.**

The architecture must never be inverted into:

> `LLM → everything else`.

That distinction defines the project.