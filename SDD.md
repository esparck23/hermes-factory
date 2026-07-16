# Spec-Driven Development (SDD) — Hermes A2A Factory

This document serves as the single source of truth for the **Hermes A2A (Agent-to-Agent) Factory** architecture, design, and developer/agent guidelines. It explains what this project is, how it is structured, and how autonomous agents should interact with it.

---

## 1. Product Overview & Purpose
The **Hermes A2A Factory** is a lightweight, high-observability agentic framework designed to automate the software development lifecycle (SDLC) for projects. It orchestrates specialized AI agents (Pi, Vibe, Qwen, Qoder) inside isolated environments using a reactive graph-based state machine.

### Key Features
- **A2A Orchestration**: Coordinates specialized tools via CLI commands.
- **Spec-Driven Quality Gates**: Validates execution outputs against strict build, test, and compilation criteria.
- **Micro-State Persistence & Handovers**: Minimizes context pollution and database bloat by recording only state transitions and agent-to-agent handover contexts in SQLite.
- **Resilient Self-Correction**: Automatically routes compilation or verification failures to diagnostics (`qwen_diagnostics`) and repair (`vibe_iteration`) nodes.

---

## 2. Directory Layout
When an agent or developer opens this repository, they will find the following structure:

```text
hermes-factory/
├── .env                  # Environment secrets & local executable paths (excluded from Git)
├── .env.example          # Template for local environment configuration
├── active.yaml           # Target projects currently selected for execution
├── projects.yaml         # Catalog of available projects and their workspace paths
├── state.py              # Pydantic or TypedDict representation of TeamState
├── nodes.py              # Orchestration nodes wrapping agent CLI invocations (Pi, Vibe, etc.)
├── routing.py            # Graph transition and routing logic
├── workflow.py           # Main engine: manages loop execution, database logging, & harnesses
├── state_checkpoint.db   # SQLite database for transitions and handovers (excluded from Git)
├── SDD.md                # This Spec-Driven Development guide
└── sandbox/              # Safe play environments and mock projects for testing the motor
    ├── demo_cli/         # Sample Python CLI project
    └── test-project/     # Sample TypeScript/Node.js project with an active .harness/
```

---

## 3. Core Component Specifications

### 3.1 State Management (`state.py`)
The system state is represented by `TeamState` (or similar dictionary structures).
- **Key Fields**:
  - `project`: Dict containing metadata of the target project under execution.
  - `project_prompt`: The refined instruction currently active.
  - `target_files`: List of files targeted for scaffolding or revision.
  - `current_code_structure`: Map of filenames to contents.
  - `quality_gate_passed`: Boolean flag denoting test/build success.
  - `error_diagnostics`: Diagnostics of compilation/test failures.
  - `agent_context`: Structured dictionary storing execution summaries per agent node.

### 3.2 Database Schema (`state_checkpoint.db`)
To prevent gigabytes of storage bloat, the motor writes only light transition checkpoints and handovers.

#### Table: `transitions`
Logs state-machine progression.
```sql
CREATE TABLE IF NOT EXISTS transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    project_name TEXT,
    step TEXT,
    status TEXT,          -- 'success' or 'failed'
    summary TEXT,         -- Last active agent's output summary (max 500 chars)
    transition_reason TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);
```

#### Table: `agent_handovers`
Stores the micro-contexts passed between agents.
```sql
CREATE TABLE IF NOT EXISTS agent_handovers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    from_agent TEXT,
    to_agent TEXT,
    context_json TEXT,    -- JSON containing specific changes and recommendations
    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);
```

### 3.3 Node Definitions (`nodes.py`)
Nodes execute external CLI tools inside the target project directory. Each node implements a timeout of **300 seconds** (5 minutes) for safety.
- **`node_pi_scaffolding`**: Spawns `pi` CLI to implement initial code structures. Injects full `STATE.md` context.
- **`node_vibe_iteration`**: Spawns `vibe` CLI to polish, refactor, or repair code. Preserves `PYTHONPATH` using `_with_vibe_env()` to avoid dependency resolution failures.
- **`node_hermes_compiler`**: Detects project type (Python/Node) and executes build and compilation checks. Sets `quality_gate_passed` to `True` if build and tests succeed.
- **`node_qwen_diagnostics`**: Spawns `qwen` CLI in case of failure to analyze build logs and suggest bug-fixes.
- **`node_qoder_audit`**: Spawns `qodercli` to run security, performance, or typing audits on the codebase.

### 3.4 Routing & Transitions (`routing.py`)
Coordinates movement through the reactive state machine:
```text
                    [Start]
                       │
             ┌─────────▼─────────┐
             │  pi_scaffolding   │◄─────────┐ (on failure)
             └─────────┬─────────┘          │
                       │ (success)          │
             ┌─────────▼─────────┐          │
      ┌─────►│  vibe_iteration   │          │
      │      └─────────┬─────────┘          │
      │                │ (any)              │
      │      ┌─────────▼─────────┐          │
      │      │  hermes_compiler  │          │
      │      └─────────┬─────────┘          │
      │                ├────────────────────┘
      │      (success) │ (failure)
      │      ┌─────────▼─────────┐
      │      │ qwen_diagnostics  │
      │      └─────────┬─────────┘
      └────────────────┘ (provides fix suggestions)
                       │
                       │ (compiler success)
             ┌─────────▼─────────┐
             │    qoder_audit    │
             └─────────┬─────────┘
                       │
                     [End]
```

---

## 4. Harness-Driven Interface (`.harness/`)
Every project managed by the Factory has a `.harness/` folder. This is the **primary channel** through which developers and agents interact with the engine.

### 4.1 `STATE.md` (The Dashboard)
The motor and agents synchronize state here.
- **Critical Field: `Acción:` / `Acción / Scope:`**: Holds high-density, precise instructions for the active step.
- **Critical Field: `🔜 Sigue:`**: Identifies the current sub-step identifier (e.g., `5.6`).
- **Critical Field: `🟢 Salud:`**: Current build health indicator (`Verde` or `Rojo`).

### 4.2 `JOURNAL.md` (Execution History)
Every run of `workflow.py` appends an entry to this file containing:
- Status of the Quality Gate.
- Summaries of actions completed by each node.
- Next steps or blocker notifications.

---

## 5. Agent Instructions: How to Interact with Hermes Factory
As an autonomous agent, you must follow these rules when developing inside or using the Hermes Factory:

1.  **Do Not Pollute Context**: Never pass entire file structures or build logs inside LLM state dictionaries. Use the `agent_context` dictionary and record clean handovers in SQLite.
2.  **Respect Scope & Exclusions**: Read `STATE.md` before making any edits. Specifically parse `Acción:` and `No tocar:`. If a file is under `No tocar`, do not touch it under any circumstance.
3.  **Harness Overriding**: Do not write hardcoded features into `workflow.py` or `nodes.py` to target individual project bugs. Fix the bugs by improving the prompts, harnessing, or CLI wrappers.
4.  **Enforce Quality Gates**: Always make sure code changes pass `npm run build`, `npx tsc --noEmit`, or `pytest` before marking a task as done.

---

## 6. How to Initialize the Repository in Another Directory
If you want to spin up a clean repository for this motor in a different directory on your system:

### Step 1: Create a Clean Target Directory
```powershell
mkdir C:\Users\Agent\dev\hermes-factory
cd C:\Users\Agent\dev\hermes-factory
```

### Step 2: Initialize Git & Configure `.gitignore`
Always initialize Git and write a proper `.gitignore` file to avoid tracking system environment secrets, large SQLite databases, or local Python package caches.
```text
# .gitignore
__pycache__/
*.pyc
.pytest_cache/
.env
state_checkpoint.db
node_modules/
dist/
```

### Step 3: Copy Core Source Files
Copy only the core orchestration files from the current folder, skipping caches and binary databases:
```powershell
Copy-Item C:\Users\Agent\hermes-factory\* -Destination C:\Users\Agent\dev\hermes-factory -Exclude "state_checkpoint.db", ".pytest_cache", "__pycache__", ".env" -Recurse -Force
```

### Step 4: Configure the New `.env` File
Create a new `.env` pointing to local binary paths. You can copy `.env.example` as a starting point.
```powershell
Copy-Item .env.example .env
```
