---
title: VerifAI
emoji: 📉
colorFrom: indigo
colorTo: gray
sdk: docker
pinned: false
---

# VerifAI

An **OpenEnv-compatible reinforcement-learning environment** for evaluating and improving AI-generated writing quality.

---

## Overview

VerifAI exposes a REST API that allows RL agents to interact with a writing evaluation environment. Agents receive writing prompts and are rewarded for producing high-quality outputs according to multi-dimensional rubrics.

---

## Environment Description

| Property | Value |
|---|---|
| Observation Space | Prompt + current output + rubric + step number |
| Action Space | `classify`, `rewrite`, or `submit` with text content |
| Reward Range | [0.0, 1.0] |
| Episode Done | Max steps reached or agent submits |

---

## Tasks

| Task | Difficulty | Max Steps | Description |
|---|---|---|---|
| `classify` | Easy | 1 | Classify output quality 0–10 |
| `rewrite` | Medium | 3 | Rewrite to satisfy rubric |
| `iterative` | Hard | 5 | Multi-turn revision under constraints |

---

## Scoring

Scores are computed by a composite grader:

| Dimension | Weight | Description |
|---|---|---|
| Safety | 0.30 | No harmful content |
| Brevity | 0.20 | Within token budget |
| Factuality | 0.25 | Claims are verifiable |
| Semantic Quality | 0.25 | Similarity to gold standard |

---

## Setup

```bash
# 1. Clone and install
git clone <repo>
cd verifai
pip install -r requirements.txt

# 2. Set your API key
export OPENAI_API_KEY=sk-...

# Optional: protect analytics endpoints
export VERIFAI_ANALYTICS_API_KEY=your-analytics-key

# 3. Run locally
uvicorn app.main:app --reload --port 7860

# 4. Validate spec
bash scripts/validate.sh

# 5. Run tests
pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/reset` | Start a new episode |
| POST | `/step` | Submit an action |
| GET | `/status` | Current session state |
| GET | `/tasks` | List all tasks |
| POST | `/grade` | Score an episode |
| POST | `/baseline/run` | Run OpenAI baseline |

## Deployment

Hosted on [Hugging Face Spaces](https://huggingface.co/spaces) using Docker SDK on port 7860.

```bash
bash scripts/deploy_hf.sh
```
