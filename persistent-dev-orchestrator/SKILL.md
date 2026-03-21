---
name: persistent-dev-orchestrator
description: Deploy, manage, and monitor self-healing AI developer agents in the background. This skill allows your OpenClaw agent to spin up isolated, persistent Tmux environments, execute multi-step PRD workflows using Ralph, and implement automated completion hooks. Essential for asynchronous coding tasks, managing parallel AI workers, and preventing silent failures during long executions.
user-invocable: true
metadata: {"openclaw":{"emoji":"⚙️","requires":{"bins":["tmux","ralphy","codex","openclaw"]}}}
---

# Persistent Dev Orchestrator

Transform your OpenClaw instance into a master project manager that autonomously oversees background coding workers. This toolkit ensures long-running agent tasks survive system disconnects, retry on failure, and accurately report their actual git commits upon completion.

## ⚠️ CORE ORCHESTRATION DIRECTIVES

As the primary OpenClaw agent, you are responsible for managing sub-agents. You must strictly adhere to these deployment rules:

### 1. Pre-Execution Validation

Never launch a worker blindly. Before initiating a deployment, you must:

* **Validate Path:** Ensure the target repository directory exists.
* **Validate State:** Execute `git status`. If the working tree is dirty, halt and ask the user how to handle uncommitted changes.
* **Validate Infrastructure:** Verify `~/.tmux/sock` will be used to prevent macOS from reaping the default temp socket.

### 2. Mandatory Isolation (No Bare Processes)

Background tasks taking longer than 30 seconds must **never** be executed directly in the shell. They must be containerized within a detached Tmux session using the exact deployment playbooks below.

### 3. The "Wake-Up" Hook Requirement

Worker agents cannot notify the user when they finish. You must append the OpenClaw `system event` hook to the end of every deployment string. This ensures the system wakes you up so you can review the worker's output.

### 4. Zero-Trust Verification

Do not trust `EXIT_CODE=0` or Ralph's internal PRD checkmarks. Worker agents often hallucinate success. When a session finishes, you must physically verify the work by executing `git log --oneline -5` and `git diff --stat`. Only report success to the user if code was actually committed.

---

## 🚀 DEPLOYMENT PLAYBOOKS

Replace all `[BRACKETED_VARIABLES]` with the specific context of the user's request.

### Playbook A: Targeted Fix Deployment

*Use for single objectives, bug fixes, or minor features without a formal PRD.*

```bash
tmux -S ~/.tmux/sock new -d -s [WORKER_ID] \
"export PATH='/opt/homebrew/bin:\$PATH'; cd [TARGET_DIR] && ralphy --codex '[OBJECTIVE_STRING]'; \
EXIT_CODE=\$?; echo EXITED: \$EXIT_CODE; \
openclaw system event --text 'Worker [WORKER_ID] finished (exit \$EXIT_CODE) in \$(pwd)' --mode now; \
sleep 999999"
```

### Playbook B: Multi-Step PRD Execution

*Use for complex feature builds driven by a Markdown checklist.*

```bash
tmux -S ~/.tmux/sock new -d -s [WORKER_ID] \
"export PATH='/opt/homebrew/bin:\$PATH'; cd [TARGET_DIR] && ralphy --codex --prd [PRD_FILENAME.md]; \
EXIT_CODE=\$?; echo EXITED: \$EXIT_CODE; \
openclaw system event --text 'Worker [WORKER_ID] finished (exit \$EXIT_CODE) in \$(pwd)' --mode now; \
sleep 999999"
```

### Playbook C: Parallel Worker Swarm

*Use to deploy multiple agents simultaneously. Warning: Only use if tasks target separate files to avoid git merge conflicts.*

```bash
cd [TARGET_DIR] && ralphy --codex --parallel --prd [PRD_FILENAME.md]
```

---

## 📡 TELEMETRY & WORKER MANAGEMENT

When the user requests an update on background tasks, use these commands to pull telemetry.

**List All Active Workers:**

```bash
tmux -S ~/.tmux/sock list-sessions
```

**Tail Worker Output (Last 20 Lines):**

```bash
tmux -S ~/.tmux/sock capture-pane -t [WORKER_ID] -p | tail -20
```

**Terminate a Rogue Worker:**

```bash
tmux -S ~/.tmux/sock kill-session -t [WORKER_ID]
```

---

## 🧠 WORKER CONFIGURATION MATRIX

If the user provides ambiguous instructions, use this logic matrix to configure the deployment:

| User Intent | Optimal Flag | Strategy |
| :--- | :--- | :--- |
| Needs structured, multi-step work | `--prd PRD.md` | Sequential execution based on checklists. |
| Needs to force past a stuck loop | `"task"` | Relies on auto-retry for transient failures. |
| Needs absolute maximum speed | `--fast "task"` | Bypasses tests/linting (warn user of tech debt). |
| Prefers Claude over Codex | `--claude "task"`| Swaps the underlying worker engine. |

---

## 🛠️ AUTONOMOUS HEALING & TRIAGE

Do not immediately bother the user if a worker fails. Attempt these self-healing steps first:

1. **Instant Worker Death:** If the session dies immediately upon creation, it is likely an auth failure. Run `codex auth login` and redeploy.
2. **False Completion Report:** If the wake-up hook fires but `git status` shows no changes, the worker failed silently. Uncheck the false completions in the PRD file and redeploy with a simpler prompt.
3. **API Rate Limiting (429s):** If a Swarm (Playbook C) hits limits, kill the swarm and redeploy the tasks sequentially using Playbook B.
4. **Environment Path Issues:** If the worker claims it cannot find a command, ensure `/opt/homebrew/bin` was successfully injected into the Tmux string.
