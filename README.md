---
title: OpenEnv Enterprise Customer Support
emoji: 🏢
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
tags:
  - openenv
  - reinforcement-learning
  - customer-support
  - enterprise-ai
  - docker
license: mit
---

<div align="center">
  <h1>🏢 OpenEnv Enterprise</h1>
  <p><b>AI Customer Support Simulation & Monitoring Center</b></p>
  
  <p><i>A mathematically constrained Reinforcement Learning environment for evaluating complex AI decision-making.</i></p>

  <a href="https://github.com/Vivek-2004V/openenv-customer-support">
    <img src="https://img.shields.io/badge/GitHub-Repository-blue?logo=github" alt="GitHub">
  </a>
  <a href="https://huggingface.co/spaces/vivekvish2004/openenv-customer-support">
    <img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-yellow" alt="Hugging Face Spaces">
  </a>
</div>

<hr />

## 🌟 Enterprise Features
This version is upgraded to **Enterprise Grade**, simulating real-company support workflows:

- 📥 **Multi-Ticket Queue**: Manage multiple active tickets in a dynamic workload simulation.
- ⏳ **SLA Monitoring**: Real-time Service Level Agreement tracking. Tickets have step-based deadlines.
- 📊 **Performance Analytics**: Session-wide reward tracking and resolution metrics.
- 🐳 **Full-Stack Docker**: Unified container serving both the React frontend and Python backend.

---

## 🏗️ Architecture
```text
.
├── app/                # FastAPI Backend (Simulation Engine)
│   ├── env.py          # Enterprise Queue & SLA Logic
│   ├── main.py         # REST API & Static File Server
├── frontend/           # Next.js 16 Dashboard
│   ├── src/app/        # Enterprise Monitoring UI
├── Dockerfile          # Multi-stage Full-Stack Build
└── inference.py        # LLM Evaluation Pipeline
```

---

## 🛠️ Enterprise Workflow
1. **Queue Initialization**: Resetting the env populates a queue of unassigned tickets.
2. **Sequential Decisioning**: The agent must Classify, Prioritize, and Respond to the head ticket.
3. **SLA Constraints**: Decisions must be made within the `sla_limit` to avoid penalties.
4. **Automated Handoff**: Resolving a ticket automatically advances the queue.

---

## 📊 Reward System (Enterprise Tuning)
| Type | Value | Condition |
| :--- | :--- | :--- |
| **Success** | `+0.4` | Full resolution with all required data. |
| **Progress** | `+0.2-0.3` | Individual correct steps (Classify/Priority). |
| **SLA Breach**| `-0.3` | Exceeding the step limit for a ticket. |
| **Penalty** | `-0.2` | Incorrect classification or poor empathy. |

---

## 🚀 Running Locally

### Option A: Docker (Recommended)
This runs the entire stack (API + Dashboard) in one command:
```bash
docker build -t openenv-enterprise .
docker run -p 7860:7860 openenv-enterprise
```

### Option B: Manual Development
**Backend:**
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 7860
```
**Frontend:**
```bash
cd frontend && npm install && npm run dev
```

---

## 📤 Deployment
This repository is optimized for **Hugging Face Spaces**. The multi-stage `Dockerfile` handles the Node.js build automatically.

To sync all updates:
```bash
git add .
git commit -m "Upgrade to Enterprise: Queue, SLA, and Docker"
git push origin main
python push_to_hf.py
```

---
<div align="center">
  Built for high-performance AI evaluation using <a href="https://github.com/OpenEnv-AI/OpenEnv">OpenEnv</a>
</div>
