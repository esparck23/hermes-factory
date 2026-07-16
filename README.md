# Hermes A2A Factory Engine

The **Hermes A2A (Agent-to-Agent) Factory** is a robust, lightweight orchestrator designed to run automated, state-driven software development workflows. By coordinating specialized LLM agents (such as Pi, Vibe, Qwen, and Qoder) inside isolated environments, the Hermes Factory automates the entire loop of code generation, compilation, automated testing, quality auditing, and self-repair.

---

## 🚀 Key Capabilities

- **State-Driven Orchestration**: Interprets high-density development instructions written inside `.harness/STATE.md` (e.g. `Acción / Scope:`) and drives specialized agents to act on them.
- **Spec-Driven Quality Gates**: Validates compiler and test results, ensuring no code is checked in unless tests are passing and TypeScript contains zero type issues.
- **Resilient Self-Correction**: If build checks fail, the engine routes execution to `qwen_diagnostics` to generate a plan, and then redirects to `vibe_iteration` for automated correction.
- **Micro-State Database**: Uses a local SQLite database (`state_checkpoint.db`) optimized to store only light state transitions and agent-to-agent handover contexts, keeping disk overhead minimal.

---

## 📁 Repository Layout

- `workflow.py`: The core orchester which loops over projects, executes active nodes, writes database records, and updates harnesses.
- `nodes.py`: Invokes the external agent CLI tools (Pi, Vibe, Qwen, Qoder) with precise arguments, timeout handlers, and isolated environmental configurations.
- `routing.py`: The transition state-machine deciding which node is executed next based on the build outputs.
- `state.py`: Formats the data structures that flow between nodes.
- `active.yaml` & `projects.yaml`: Configures which projects are processed.
- `SDD.md`: Detailed Spec-Driven Development guide outlining DB schemas, node architectures, and guidelines for other AI agents.
- `sandbox/`: Contains dummy and test environments (`test-project`, `demo_cli`) used to run integration tests on the motor.

---

## 🛠️ Setup Instructions

To host and run this repository in a clean directory on your system, follow the step-by-step setup guide below.

### 1. Initialize Git in Your Directory
```powershell
# Create your target folder (e.g. C:\Users\Agent\dev\hermes-factory)
mkdir C:\Users\Agent\dev\hermes-factory
cd C:\Users\Agent\dev\hermes-factory

# Initialize a clean Git repository
git init -b main
```

### 2. Copy Source Code (Excluding Databases and Caches)
Run this command from your current environment to copy only the untracked, clean source files from the current path:
```powershell
Copy-Item C:\Users\Agent\hermes-factory\* -Destination . -Exclude "state_checkpoint.db", ".pytest_cache", "__pycache__", ".env" -Recurse -Force
```

### 3. Setup Your Local Environment `.env`
Copy the `.env.example` file to `.env` and fill in your absolute paths to the agent CLI executables:
```powershell
Copy-Item .env.example .env
```
Open `.env` and configure paths (e.g., node npm globals, path environments).

---

## 📝 Usage

To start orchestrating your active projects:
```powershell
python workflow.py
```

Check the `SDD.md` for a comprehensive breakdown of the internal architecture, database schema, and node execution graphs.
