# BRIEFING — 2026-07-16T05:30:00+07:00

## Mission
Fully implement the CodeAvatar project by managing the parallel E2E Testing and Implementation Tracks.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: /home/thienvu/workspace/CodeAvatar/.agents/orchestrator/
- Original parent: main agent (Sentinel)
- Original parent conversation ID: a1b019da-a70d-4c68-8f5f-b2d375f0ab9c

## 🔒 My Workflow
- **Pattern**: Project
- **Scope document**: /home/thienvu/workspace/CodeAvatar/PROJECT.md
1. **Decompose**: Decompose the user request into two tracks: E2E Testing (test suite creation and verification) and Implementation (building 5 distinct milestones sequentially).
2. **Dispatch & Execute**:
   - **Delegate (sub-orchestrator)**: Spawn sub-orchestrators for the E2E Testing Track and the Implementation Track.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (sub-orchestrators only, last resort)
4. **Succession**: Self-succeed at 16 spawns. Write handoff.md, spawn successor, terminate timers.
- **Work items**:
  1. Initialize project files [done]
  2. Spawn E2E Testing Track sub-orchestrator [pending]
  3. Spawn Implementation Track sub-orchestrator [pending]
  4. Synthesize results and report completion [pending]
- **Current phase**: 2
- **Current focus**: Launching the dual-track sub-orchestrators.

## 🔒 Key Constraints
- Vietnam language preference for user/parent communication.
- Markdown headers in English.
- No direct code writing; always delegate code writing and execution to specialized subagents.
- VRAM unloading and isolated child multiprocessing.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.

## Current Parent
- Conversation ID: a1b019da-a70d-4c68-8f5f-b2d375f0ab9c
- Updated: not yet

## Key Decisions Made
- Organized the project into a parallel dual-track system: one for E2E Testing to build requirement-driven tests, one for Implementation to build features.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| E2E Testing Orch | self | Build E2E test suite | stale | 23915443-db0e-48e3-a2ee-5f51e0181fc4 |
| Implementation Orch | self | Implement Milestones 1-5 | stale | 0d8a74a8-c026-4c32-895b-7d7710a34576 |
| E2E Testing Orch | self | Build E2E test suite | in-progress | 70aa277d-c46f-4bf9-b406-23134134c402 |

## Succession Status
- Succession required: no
- Spawn count: 3 / 16
- Pending subagents: [70aa277d-c46f-4bf9-b406-23134134c402]
- Predecessor: e8f285cd-07e9-4ddc-bfa6-69fc04f08ea5
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: f31bc044-6030-44c7-80c5-334c494d4d59/task-23
- Safety timer: none
- On succession: kill all timers before spawning successor
- On context truncation: run `manage_task(Action="list")` — re-create if missing

## Artifact Index
- `/home/thienvu/workspace/CodeAvatar/PROJECT.md` — Global architecture, code layout, and milestone definitions.
- `/home/thienvu/workspace/CodeAvatar/.agents/orchestrator/plan.md` — Project implementation plan.
- `/home/thienvu/workspace/CodeAvatar/.agents/orchestrator/progress.md` — Detailed step progress and liveness heartbeat.
- `/home/thienvu/workspace/CodeAvatar/.agents/orchestrator/context.md` — Environment variables and file maps.
