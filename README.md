---
title: VerifAI
emoji: 🔍
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
tags:
  - openenv
  - rl-environment
  - ai-evaluation
  - writing-quality
  - reinforcement-learning
short_description: OpenEnv-compatible RL environment for AI writing evaluation
---

# 🔍 VerifAI

An **OpenEnv-compatible reinforcement-learning environment** that grounds AI agents in the real-world task of **evaluating and improving AI-generated writing quality**. Agents receive raw text and are challenged to refine it according to strict, multi-dimensional rubrics.

[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/SohamLone77/verifAI)
[![OpenEnv Specification](https://img.shields.io/badge/OpenEnv-Compatible-green)](https://github.com/openenv-hub/openenv)

---

## 🌟 Motivation: Real-World Utility

VerifAI is designed to train and evaluate RL agents on a **genuine enterprise problem**: automated content moderation and brand compliance. 
Instead of toy grid-worlds, VerifAI challenges agents to act as **AI Editors**. Agents must read a draft, assess it against a `Rubric` (Safety, Brevity, Factuality, Brand Voice), and successfully rewrite it. This addresses a massive real-world gap where LLMs often generate plausible but non-compliant or verbose outputs that require structured alignment.

---

## 🏗️ Environment Architecture

VerifAI tightly follows the OpenEnv specification, enforcing state through typed Pydantic models.

### Action and Observation Spaces

| Space | Structure / Schema |
|---|---|
| **Observation** | Model containing the `prompt`, the `current_output` (text so far), a strict `rubric` constraints object, and `step` count. |
| **Action** | Action model enforcing an `action_type` (`classify`, `rewrite`, `submit`), the string `content`, and optional `reasoning` steps. |
| **Reward** | Range `[0.0, 1.0]`. Smoothly shaped based on text improvement. |

### Semantic & Rule-Based Graders
To ensure deterministic and fast grading (no LLM-as-a-judge latency/hallucinations), VerifAI utilizes a 100% reproducible **Composite Grader**:
1. **Rubric Grader**: Rapid rules-based evaluation using regex and yaml configurations for Brand Voice, Safety terminology, and Token budgets.
2. **Semantic Grader**: Uses local `sentence-transformers` (`all-MiniLM-L6-v2`) to compute cosine similarity between the agent's rewrite and the underlying prompt/gold-standard task guidelines.

---

## 🎯 Tasks & Difficulty Progression

VerifAI ships with three escalating tasks, tested against a deterministic suite of environments:

| Task Name | Difficulty | Description | Objective |
|---|---|---|---|
| `classify` | **Easy** (Max 1 Step) | Evaluator Simulation | The agent must output a valid JSON classification of the provided text, judging quality 0–10. |
| `rewrite` | **Medium** (Max 3 Steps) | Direct Revision | The agent is given a flawed text and must edit it to satisfy all rubric constraints. |
| `iterative` | **Hard** (Max 5 Steps) | Multi-turn Agentic Revision | The agent handles highly non-compliant drafts requiring step-by-step reasoning and multiple rounds to fit strict token boundaries and brand rules. |

### Reward Shaping Dynamics
VerifAI avoids sparse 0-or-1 rewards. The reward function includes:
- **Progress Bonus**: Rewards the agent dynamically for improving the semantic score in successive steps.
- **Step Penalty**: A small negative decay (e.g., -0.01) to encourage brevity.
- **Chain of Thought (CoT) Bonus**: If the agent utilizes the `reasoning` trace field, they receive a slight algorithmic bonus.
- **Safety Penalty**: Significant point deductions for producing explicitly harmful keywords.

---

## 📊 Baseline Evaluation

VerifAI was proven against **frontier models**. The baseline inference script is located in the root repository (`inference.py`) and utilizes standard OpenAI compatiblity. 

**Model:** `Qwen/Qwen2.5-72B-Instruct` (via Hugging Face Serverless)

| Task | Difficulty | Avg Reward | Success Rate |
|---|---|---|---|
| `classify` | Easy | **0.90** | 100% |
| `rewrite` | Medium | **0.90** | 100% |
| `iterative` | Hard | **0.92** | 100% |

*Grading is 100% deterministic.* To rapidly reproduce these exact scores:
```bash
export HF_TOKEN=your-hf-token
python inference.py
```

---

## 🚀 Setup & Execution

### Running Locally (Docker)

VerifAI comes fully containerized and passes OpenEnv validation out of the box.

```bash
git clone https://huggingface.co/spaces/SohamLone77/verifAI
cd verifAI

# Build the docker container
docker build -t verifai-env .

# Run the environment
docker run -p 7860:7860 verifai-env
```

### Automatic Validation
Test VerifAI against the OpenEnv spec locally:
```bash
bash scripts/validate.sh
```

### Environment API Endpoints

Once running, the core RL loop operates strictly over standard endpoints:

| Method | Endpoint | Description |
|---|---|---|
| **POST** | `/reset` | Initializes a new episode, generating `session_id` and initial `Observation`. |
| **POST** | `/step` | Submit an `Action`. Returns next `Observation`, `Reward`, `done`, and `info`. |
| **GET** | `/state/{id}`| Retrieve the full Pydantic state model for an episode. |
| **GET** | `/tasks` | List available RL tasks configured in `openenv.yaml`. |

---

## 🌐 Deployment Details

VerifAI is designed to natively run on **Hugging Face Spaces**.
The provided `Dockerfile` leverages a non-root user (`uid=1000`) and safely pre-downloads sentence-embedding weights, ensuring instant startup for judge evaluations. 

Access the live space here: **[SohamLone77/verifAI](https://huggingface.co/spaces/SohamLone77/verifAI)**
