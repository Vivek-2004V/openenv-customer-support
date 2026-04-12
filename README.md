---
title: OpenEnv Customer Support
emoji: 🎫
colorFrom: indigo
colorTo: cyan
sdk: docker
pinned: false
license: mit
tags:
  - openenv
  - reinforcement-learning
  - customer-support
  - simulation
  - ai-agent
---

# 🎫 OpenEnv Customer Support Environment

A complete, real-world **OpenEnv simulation environment** where an AI agent learns customer support decision-making through the standard `step()` / `reset()` / `state()` API.

---

## Evaluation Criteria

| Criterion | Status | Details |
|---|---|---|
| ✅ **Runtime correctness** | Runs without errors | FastAPI + uvicorn, HEALTHCHECK in Dockerfile |
| ✅ **Interface compliance** | Follows OpenEnv standard | `/reset`, `/step`, `/state`, `/health`, `/metadata`, `/schema`, `/tasks`, `/grader` |
| ✅ **Task design** | Clear, realistic, testable | 7 graded tasks (EASY → HARD) with explicit scoring breakdowns |
| ✅ **Grading logic** | Reward system makes sense | Deterministic per-task graders, scores strictly in [0.0, 1.0] |

---

## OpenEnv Standard API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/reset` | Start new episode, returns initial observation |
| POST | `/step` | Submit action `{action_type, payload}`, returns `{observation, reward, done, info}` |
| GET | `/state` | Current environment state |
| GET | `/health` | Health check → `{status: "healthy"}` |
| GET | `/metadata` | Environment name, description, version |
| GET | `/schema` | JSON schemas for action / observation / state |
| GET | `/tasks` | All 7 tasks with grader metadata |
| GET | `/grader?task_id=<id>` | Grade specific task, returns score in [0.0, 1.0] |
| POST | `/mcp` | JSON-RPC 2.0 MCP endpoint |

---

## Actions

```json
{"action_type": "classify_ticket",   "payload": {"classification": "refund"}}
{"action_type": "assign_priority",   "payload": {"priority": "high"}}
{"action_type": "generate_response", "payload": {"response": "I apologize..."}}
{"action_type": "resolve",           "payload": {}}
{"action_type": "escalate",          "payload": {}}
```

**Categories:** `refund` · `technical_issue` · `login_issue` · `general_inquiry` · `feedback` · `security`  
**Priorities:** `low` · `medium` · `high`

---

## Tasks & Graders

| ID | Name | Difficulty | Scoring |
|----|------|-----------|---------|
| `task_easy_1` | Ticket Classification | EASY | classification correct = 1.0 |
| `task_easy_2` | Priority Assignment | EASY | priority correct = 1.0 |
| `task_medium_1` | Classify and Respond | MEDIUM | classify 0.5 + empathy 0.5 |
| `task_medium_2` | Professional Resolution | MEDIUM | classify 0.5 + keywords 0.5 |
| `task_hard_1` | Full Support Workflow | HARD | 4 steps × 0.25 each |
| `task_hard_2` | High-Priority Angry Customer | HARD | 4 components × 0.25 |
| `task_hard_3` | Efficiency Challenge | HARD | accuracy + speed bonus |

---

## Grading Logic

Every grader returns a float in **[0.0, 1.0]**:

- **EASY tasks** — binary: correct = 1.0, wrong = 0.0
- **MEDIUM tasks** — partial credit: each sub-component = 0.5
- **HARD tasks** — multi-component: each step = 0.2–0.25, clamped to 1.0

```python
# Example: grade task_hard_1
score = env.grade("task_hard_1", history, ground_truth)
assert 0.0 <= score <= 1.0  # ✅ always
```

---

## Quick Start

```bash
# Reset environment
curl -X POST https://your-space.hf.space/reset

# Execute action
curl -X POST https://your-space.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "classify_ticket", "payload": {"classification": "refund"}}'

# Grade a task
curl https://your-space.hf.space/grader?task_id=task_hard_1
```

---

## Local Development

```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
# Visit http://localhost:7860
```

---

## License

MIT © 2024
