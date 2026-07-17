# Collaboration & Contribution Protocol — Hermes A2A Factory

This document defines the specialized workflow, branching strategy, and safety protocols for human developers and AI agents collaborating on the **Hermes A2A Factory** repository.

---

## 1. Branching Strategy
We use a **GitHub Flow-inspired** branching model optimized for Agent-to-Agent (A2A) integration. 

- **`main`**: The production-ready, stable version of the motor. Direct pushes to `main` are **strictly prohibited** for collaborators and agents.
- **`develop`**: The integration branch. All feature branches must branch off `develop` and be merged back into `develop` via Pull Requests (PRs).
- **`feature/*` or `agent/*`**: Temporary branches for developing specific nodes, features, or fixing bugs.
  - *Example*: `feature/new-qwen-prompt` or `agent/vibe-timeout-patch`.

---

## 2. Collaboration Protocol

```text
       [develop] ───────────────────────────► [develop] (Integrated)
          │                                      ▲
          │ (branch off)                         │ (PR + Quality Gate)
          ▼                                      │
   [feature/your-patch] ───► [Commit/Push] ──────┘
```

### 2.1 For Human Collaborators
1.  **Always branch off `develop`**:
    ```powershell
    git checkout develop
    git pull origin develop
    git checkout -b feature/your-feature-name
    ```
2.  **Write atomic commits**: Keep changes focused on a single module or issue.
3.  **Run Quality Checks**: Before submitting a PR, make sure the engine's integration tests still pass.
4.  **Open a Pull Request**: Target `develop` as the base branch.

### 2.2 For Autonomous Agents (A2A Team)
Autonomous agents interacting with this repository must adhere to the following machine-readable rules:

1.  **Checkout Feature Branch**: When tasked with a repair or new feature, the agent must spawn a branch matching `agent/<task-name>` or `fix/<blocker-id>`.
2.  **Sandbox Isolation**: All testing during development must be performed inside `sandbox/` or using mock projects. Do **not** run execution tests on active production repos while on feature branches.
3.  **Verify local compilation**: The agent must run compilation and linting tests:
    ```powershell
    python -m py_compile workflow.py nodes.py routing.py state.py
    ```
4.  **Handover Record**: If the task is completed by an agent, it must output a brief JSON summary of changed files and push the branch to the remote origin for review.

---

## 3. Pull Request (PR) Quality Gate
To merge any branch into `develop` or `develop` into `main`, the changes must pass the **Factory Quality Gate**:

1.  **No Type Errors**: If TypeScript files are modified (in sandbox or assets), `npx tsc --noEmit` must return `0` errors.
2.  **No Compiler Failures**: Python source code must compile perfectly without syntax errors.
3.  **No Unsaved SQLite Bloat**: Ensure `state_checkpoint.db` is **never** committed or tracked.
4.  **No Secret Leaks**: Verify that `.env` is omitted and untracked.

---

## 4. Conflict Resolution Protocol
When conflicts arise in YAML configurations (`projects.yaml`, `active.yaml`):

- **`active.yaml` conflicts**: Always default to the collaborator's active settings or merge them under separate array elements.
- **`projects.yaml` conflicts**: Keep all projects listed; do not delete catalog entries created by other collaborators.

---

## 5. Environment Setup (Required for All Collaborators)

Both human developers and autonomous agents **must** perform the following setup steps after cloning the repository. This ensures the Hermes A2A Factory motor can locate CLI tools and required dependencies in any environment.

### 5.1 Install Python Dependencies

The project uses `python-dotenv` for environment management, `pyyaml` for configuration, and `pytest` for tests. Install them via:

```powershell
pip install -r requirements.txt
```

If `pip` is not found, use:

```powershell
python -m pip install -r requirements.txt
```

### 5.2 Configure `.env` File

The motor loads CLI paths dynamically from environment variables defined in a `.env` file at the project root.

1. Copy the template:
   ```powershell
   copy .env.example .env
   ```
2. Edit `.env` and register the correct paths for your local CLI installations:
   ```text
   CLI_PI=C:\path\to\pi.cmd
   CLI_VIBE=C:\path\to\vibe.exe
   CLI_QWEN=C:\path\to\qwen.cmd
   CLI_QODERCLI=C:\path\to\qodercli.exe
   CLI_EXTRA_PATHS=C:\path1;C:\path2
   ```
3. The motor validates each path on startup. If a path does not exist, it falls back to the bare command name (assuming it is in the system `PATH`).

### 5.3 Verify the Setup

Run a quick smoke test to confirm `nodes.py` loads paths correctly:

```powershell
python -c "from nodes import CLI_PATHS, EXTRA_PATHS; print(CLI_PATHS); print(EXTRA_PATHS)"
```

If the output shows valid paths and no `[WARNING]` messages are printed, the setup is correct.

### 5.4 Agents Must Also Follow This Protocol

Autonomous agents must:
1. Detect the presence of `.env` at startup. If missing, **abort** and report a configuration error.
2. Never hardcode absolute paths to `C:\Users\Agent\...` in their code. Use the `CLI_PATHS` dictionary from `nodes.py`.
3. Run `pip install -r requirements.txt` as part of their initial environment handshake.
