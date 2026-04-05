# Junior Apogee App

Junior Apogee is an evaluation and QA workbench for multi-agent AI systems.
It includes a Flask dashboard, layered evaluation logic, governance checks,
and reporting scripts for local experimentation.

## Current Source of Truth

The active implementation lives in `src/junior_apogee/` and the dashboard entry
point is the repository-root `app.py`.

The top-level `junior_apogee_app/` package is still present for older examples
and tests, but new work should target the `src/` implementation.

## What Is In This Repo

- `app.py` - dashboard backend and demo API routes
- `src/junior_apogee/` - models, evaluation engine, governance, metrics, config
- `config/` - YAML definitions for agents, metrics, and task families
- `scripts/run_eval.py` - pytest wrapper for running subsets of the suite
- `scripts/generate_report.py` - synthetic report generator
- `tests/` - unit, integration, and legacy compatibility tests

## Quick Start

```bash
git clone https://github.com/Flickerflash/junior-apogee-app.git
cd junior-apogee-app
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## Run Tests

```bash
python -m pytest tests -v
```

Or use the helper script:

```bash
python scripts/run_eval.py --layer all -v
```

## Generate a Sample Report

```bash
python scripts/generate_report.py --tasks 5 --output reports/report.json
```

## Package Smoke Check

The packaged CLI exposes a simple info command:

```bash
python -m junior_apogee info
```

## Configuration

- Copy `.env.example` to `.env` if you want local environment variables.
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` enables LLM-judge features.
- YAML configuration lives in `config/agents.yaml`, `config/metrics.yaml`, and
  `config/task_families.yaml`.

## Docker

A basic `Dockerfile` is included.

```bash
docker build -t junior-apogee-app .
docker run -p 5000:5000 junior-apogee-app
```

There is currently no `docker-compose.yml` in the repository.
