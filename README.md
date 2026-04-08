# AI Customer Support Decision-Making Environment (OpenEnv)

## Environment Description
This is a mathematically constrained OpenEnv Customer Support simulation. It simulates real-world workflows encompassing complex decision-making processes for an AI customer support agent. The environment maps dynamic ticket properties (sentiment, issues) and evaluates sequential agent logic to determine correct problem resolutions across constrained pipelines.

## Action Space
The AI agent interacts with the environment sequentially by emitting precise JSON payloads defined dynamically inside string schemas.

**Available Actions:**
- `classify_ticket`: Evaluates string. Payload mapping: `{"classification": "refund" | "general_inquiry" | "login_issue" | "feedback"}`
- `assign_priority`: Assigns structural tier. Payload mapping: `{"priority": "low" | "medium" | "high"}`
- `generate_response`: Drafts contextual replies to tickets. Enforces checking `sentiment` logic constraint requirements (e.g., apologies). Payload mapping: `{"response": "<text>"}`
- `escalate`: Maps directly to manual priority bypass. Empty payload: `{}`
- `resolve`: Pipeline completion call mapped to constraints checking complete scenario data. Empty payload: `{}`

## Observation Space
State mapping delivers deterministic JSON payload snapshots back to the interacting agent across the workflow sequence.

**State Fields Include:**
- `ticket_text`: Read-only simulated user input sequence string.
- `sentiment`: Customer evaluation mapped (e.g., `angry`, `neutral`, `happy`).
- `priority`: Active assignment tracker (`null` until categorized).
- `status`: Global environment variable matching `open` or `closed` lifecycle mapping.
- `steps_taken`: Numeric iteration tracker mapping execution costs.
- `classification`: Evaluated class.
- `response`: Text payload caching assigned generated scripts.

## Task Descriptions
The environment exposes explicit evaluation goals mapping standard deterministic task metrics (`0.0` - `1.0`):

- **EASY** (`task_easy_1`): Only classify the issue correctly. 
- **MEDIUM** (`task_medium_1`): Classify the ticket completely and generate an appropriate text response (measuring conditional logic like providing empathy for an explicitly 'angry' sentiment).
- **HARD** (`task_hard_1`): The agent structurally navigates the entire pipeline: 1. Correctly classify mapping 2. Assign priority mappings accurately 3. Emit valid appropriate responses 4. Correctly resolve the closed ticket state.

## Reward Design
Densely structured continuous math map designed for precision agent behavior shaping:

**Sequential Rewards (Partial Progress):**
- **`+0.3`**: Correct ticket classification.
- **`+0.2`**: Accurate priority assignment.
- **`+0.2`**: Successful appropriate response generation.
- **`+0.3`**: Officially verified constraint-approved ticket structural resolution.

**Penalties:**
- **`-0.2`**: Punishes specifically wrong actions (assigning the wrong classification, failing empathy mappings, bypassing procedures).  
- **`-0.1`**: Punishment for immediately duplicating/repeating explicit prior script actions iteratively.
- **`-0.1`**: Incurred purely per sequential step count scaling execution delays to promote processing speed organically.

## Setup Instructions
Use pip explicitly isolating a lightweight requirement instance natively natively configuring local systems:

```bash
pip install -r requirements.txt
```

Start the interactive API server natively linking locally:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 7860
```
### Running Via Docker (Hugging Face Ready)
This build incorporates standard non-root target configs enabling seamless capability deploys onto HF. 
```bash
docker build -t openenv-support .
docker run -p 7860:7860 openenv-support
```

## How to Run Inference (Hugging Face / OpenAI)
Trigger our automated evaluate pipeline structurally invoking evaluations cleanly recording constraints logic directly via precise print hooks dynamically validating execution.

```bash
export MODEL_NAME="meta-llama/Meta-Llama-3-8B-Instruct"
export HF_TOKEN="hf_..."
python inference.py --task task_hard_1
```

## Push to Hugging Face Hub
A helper script allows you to rapidly publish your entire codebase straight out into your Hugging Face space repository. 

Run the automated publisher to upload this space seamlessly into `vivekvish2004/openenv-customer-support`:
```bash
python push_to_hf.py
```
*(This gracefully detects existing tokens and ignores large bloat directories like node_modules to ensure a fast, clean upload!)*
