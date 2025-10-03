# Agent-Gym POC

FastAPI microservice AGENT (LangChain/LangGraph) that orchestrates an agent to analyze training metrics.
The AGENT calls the APP (another FastAPI microservice) to fetch workout stats, computes KPIs, and returns human-readable conclusions.

Goal: demonstrate a realistic agent + tools flow decoupled from the app, with orchestration, traceability, and solid deployment practices.


## TL;DR

* Frontend → APP

* AGENT  → calls APP

Tools in AGENT:

* fetch_stats → GET /api/v1/statistics/{user_id}/stats

* compute_kpis → KPIs by muscle group, volume, RPE/RIR, ACWR, alerts

* compute_conclusions → recommendations based on goal (e.g., strength, hypertrophy)

* Orchestration with LangGraph (deterministic and robust)


## Architecture

```bash
Frontend
   | ^
   | |
   v |
AGENT (FastAPI + LangGraph + Tools + LLM)
   | ^
   | |
   v |
APP (FastAPI)  --->  /api/v1/statistics/{user_id}/stats


AGENT: receives user questions, orchestrates tools, and uses an LLM to explain/summarize.
APP: exposes REST endpoints. No AI dependency.

```

## Requirements

* Docker & Docker Compose

* Python 3.10+ (optional for local dev without Docker)

* OpenAI API Key (if using OpenAI) or an Ollama server with a small model (if using Ollama)


## Enviorment

Create an .env

```bash
# Orchestration
AGENT_MODE=agentic     # use non deterministic graph

# LLM (choose one)
LLM_PROVIDER=openai    # openai | ollama
OPENAI_API_KEY=sk-...    # required if LLM_PROVIDER=openai

# Ollama (if you use it)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M

# From inside the AGENT container, call APP by service name + internal port
STATS_API_BASE_URL=http://api:8000
````

## Installation

Simply run the docker command

```bash
docker compose up -d --build
```

To ensure that everything works fine just run.

```bash
curl http://localhost:8000/health
# -> {"ok": true}
```

## Usage

To test the agent 

```curl
curl -X POST http://localhost:9000/v1/agent/summary \
  -H "Content-Type: application/json" \
  -H "X-Thread-ID: demo-123" \
  -d '{
    "user_id": "123",
    "start": "2025-09-01",
    "end": "2025-09-29",
    "goal": "Fuerza",
    "question": "El volumen de entrenamiento es adecuado?"
  }'

```

Example response

```json
{
  "answer": "Aumentar el volumen de entrenamiento en pecho y hombros...",
  "evidence": {
    "by_muscle": [
      {"muscle_group": "LEGS", "kg": 27720.0, "series": 35, "reps": 229, "rpe_mean": 8.0, "rir_mean": 2.0},
      {"muscle_group": "BACK", "kg": 8490.0, "series": 24, "reps": 168, "rpe_mean": 8.0, "rir_mean": 2.0}
    ],
    "alerts": []
  },
  "sources": [
    {"type": "api", "endpoint": "/api/v1/statistics/123/stats", "meta": {}}
  ],
  "usage": {"mode": "graph"}
}
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.


## End-to-end DEMO (Front → Agent → App)

![Alt Text](https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExMnEyeTc0ZjIyZG94M2QwOHo0c29wcms0bjMzZmp4enJiejBpd2ZpZyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/nMaJEWDRjhNw8uewCt/giphy.gif)

