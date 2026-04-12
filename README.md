---
title: "OpenEnv Customer Support"
emoji: "🎫"
colorFrom: "indigo"
colorTo: "blue"
sdk: "docker"
pinned: false
license: "mit"
tags:
  - openenv
  - reinforcement-learning
  - customer-support
  - enterprise-ai
  - decision-making
  - nlp
---

# 🎫 OpenEnv Customer Support Environment

A high-fidelity, real-world **OpenEnv simulation environment** designed to train and benchmark AI agents in enterprise customer support decision-making. 

Implements the full OpenEnv `step()` / `reset()` / `state()` API with standard Pydantic models.

---

## 💡 Motivation & Real-world Relevance

In modern enterprise operations, customer support is not just about answering questions—it's about complex multi-step decision-making under SLA (Service Level Agreement) pressure. Handling a support queue requires consistent logic, empathetic communication, and accurate technical classification.

This environment provides a structured sandbox for AI agents to master:
- **Triage**: Accurately classifying issues to route to the correct engineering teams.
- **Prioritization**: Balancing customer sentiment with business urgency.
- **Empathy**: Nuanced response generation for frustrated or panicked users.
- **Workflow Integrity**: Ensuring all steps (category, priority, response) are completed before resolution.

---

## 🛠️ Environment Specification

### Action Space

The agent interacts with the environment using a typed `Action` model.

| Action Type | Payload Description | Allowed Values |
|-------------|---------------------|----------------|
| `classify_ticket` | Categorize the issue | `refund`, `technical_issue`, `login_issue`, `general_inquiry`, `feedback`, `security` |
| `assign_priority` | Set business priority | `low`, `medium`, `high` |
| `generate_response` | Draft a text response | Any string (e.g., "I'm sorry for the inconvenience...") |
| `search_kb` | Query internal policy | Returns technical/billing policy facts |
| `ask_clarification`| Request missing info | Used for vague tickets to unlock resolution |
| `resolve` | Close the ticket | `{}` (Requires classification, priority, and response) |
| `escalate` | Direct to senior level| `{}` (Appropriate for high-sentiment/emergency) |

### Observation Space

The environment returns a comprehensive state dictionary in every step.

| Key | Type | Description |
|-----|------|-------------|
| `ticket_text` | `string` | The raw customer inquiry text. |
| `sentiment` | `string` | Customer mood: `angry`, `panicked`, `curious`, `happy`, `concerned`, `neutral`. |
| `status` | `string` | Lifecycle state: `open`, `closed`, `session_complete`. |
| `priority` | `string` | The currently assigned priority. |
| `classification`| `string` | The currently assigned category. |
| `steps_taken` | `int` | Number of actions performed on the current ticket. |
| `sla_limit` | `int` | Maximum steps allowed for this ticket type. |
| `total_reward` | `float` | Cumulative reward across the entire 3-ticket session. |
| `last_step_status`| `string` | Result of the previous action: `success`, `failed`, `neutral`. |
| `kb_context` | `string` | Contains the most recent Knowledge Base search result. |
| `is_clarified` | `bool` | True if the agent has asked for clarification. |

---

## 📈 Reward Function

The environment utilizes a **dense reward function** to provide guidance throughout the trajectory:

- **Correct Classification**: `+0.35` (Penalty for wrong: `-0.20`)
- **Correct Priority**: `+0.25` (Penalty for wrong: `-0.15`)
- **Professional Response**: `+0.20`
  - *Empathy Requirement*: Responses to upset/panicked customers must contain empathy keywords.
- **Successful Resolution**: `+0.40`
  - *SLA Penalty*: `-0.25` if resolved after the SLA step limit.
- **Efficiency Penalty**: `-0.02` per step to encourage direct, non-redundant behavior.

---

## 🏁 Baseline Benchmarks

Verified scores from the consolidated validation suite.

| Agent Type | Avg. Total Reward | Queue Completion Rate | Evaluation |
|------------|-------------------|-----------------------|------------|
| **Random Agent** | `-0.85` | `0%` | Failed |
| **Simple Heuristic** | `1.45` | `45%` | Moderate |
| **Perfect Baseline** | `3.36` | `100%` | Excellent |

---

## 🚀 Getting Started

### Installation

```bash
# Clone and install dependencies
git clone <repo_url>
pip install -r backend/requirements.txt
```

### Running Locally

1.  **Start the Backend**:
    ```bash
    python3 backend/main.py
    ```
2.  **Launch the Dashboard**:
    ```bash
    cd frontend && npm install && npm run dev
    ```

### Running Inference

Use the standard OpenEnv inference script to run your model (requires `OPENAI_API_KEY`):
```bash
python scripts/inference.py
```

---

## 🧪 Evaluation & Grading

The environment includes **10 deterministic graders** spanning Easy, Medium, Hard, and Extreme difficulties.

- **EASY Tasks**: Single-attribute checks (e.g., correct classification).
- **MEDIUM Tasks**: Partial workflow checks (e.g., Priority + Response empathy).
- **HARD Tasks**: Full end-to-end lifecycle resolution under SLA constraints.
- **EXTREME Tasks**: Multi-turn workflows requiring Knowledge Base (KB) lookups, cross-referencing policies, and clarification of vague customer inputs.

---

## 🏆 Judging Criteria & Technical Compliance

| Criterion | Implementation in Customer Support Env |
|-----------|----------------------------------------|
| **Real-world Relevance** | Simulates complex enterprise support workflows (SLA, Triage, Policy). |
| **Complexity** | 10 hand-crafted tasks with tiered difficulty (Easy to Extreme), multi-step trajectories (up to 12 steps), and state-dependent logic. |
| **Standard Compliance** | 100% adherence to OpenEnv `step()`/`reset()`/`state()` API. Verified via `openenv validate`. |
| **Robustness** | Session-based isolation for multi-agent evaluation and error-resilient inference pipeline. |
| **Realism** | Uses 12 high-fidelity customer scenarios with dynamic sentiment decay (customers get angrier over time). |

---

## 📋 Detailed Task Matrix

| Task ID | Name | Difficulty | Core Objective | Evaluation Metric |
|---------|------|------------|----------------|-------------------|
| `task_easy_1` | Classification | EASY | Categorize issue correctly | Classification match (0.99) |
| `task_easy_2` | Priority | EASY | Set correct priority | Priority match (0.99) |
| `task_medium_1`| Empathy Check | MEDIUM | Classify + Respond | Classification + Empathy keywords |
| `task_medium_2`| Professionalism| MEDIUM | Classify + Solve | Classification + Solution keywords |
| `task_hard_1` | Full Lifecycle | HARD | End-to-end resolution | Success on all 4 steps (0.25 each) |
| `task_hard_2` | De-escalation | HARD | High-priority anger | High Priority + Empathy keywords |
| `task_hard_3` | SLA Challenge | HARD | Efficiency under pressure| Bonus for fewer steps (≤4) |
| `task_extreme_1`| Policy Lookup | EXTREME | Use KB for decision | KB match + Policy citation |
| `task_extreme_2`| Vague Input | EXTREME | Clarify before resolve | `ask_clarification` call requirement |
| `task_extreme_3`| Security P0 | EXTREME | Handle breach | Security KB + High Priority + Escalate |

---

## 🛡️ Reliability & Concurrency

### Session Isolation
The backend supports concurrent evaluation of multiple agents. By using the `session_id` query parameter, each evaluator gets a dedicated, isolated environment instance to prevent state crosstalk.

### Robust Inference
The provided `inference.py` includes built-in retry logic (max 3 attempts) and multi-pass JSON validation. This ensures the evaluation pipeline is resilient to transient LLM failures or malformed model outputs.

---

## 📄 License

MIT © 2024
