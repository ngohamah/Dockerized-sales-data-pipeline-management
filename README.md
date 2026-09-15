# Mini Data Platform (Dockerized)

![CI/CD](https://github.com/<OWNER>/<REPO>/actions/workflows/main.yml/badge.svg)
<!-- Replace <OWNER>/<REPO> once this repo is pushed to GitHub. -->

A small, self-contained data platform that shows the full data lifecycle —
**collection → processing → storage → visualization** — running entirely in
Docker containers.

## What it does, in plain terms

1. A **data generator** creates fake sales orders (customer, product, amount, date) and drops them as a CSV file into **MinIO** (an S3-compatible file store).
2. An **Airflow** pipeline notices the new file, cleans it up (removes bad or duplicate rows), and loads the good rows into a **PostgreSQL** database.
3. **Metabase** connects to that database and turns the data into charts anyone can read — revenue over time, orders by category, and so on.

```
 [Data Generator]
        │  writes one CSV batch
        ▼
 [MinIO: raw-data/incoming/]
        │  sensed by the Airflow DAG
        ▼
 [Airflow: clean → validate → de-duplicate]
        │  loads clean rows
        ▼
 [PostgreSQL: app_data.sales_records]
        │  queried by
        ▼
 [Metabase dashboard]
```

## Prerequisites

- Docker and Docker Compose v2 (`docker compose version`)
- Python 3.11 (only needed to run tests/lint outside Docker)

## Setup

1. Copy the environment template and fill in real values:
   ```bash
   cp .env.example .env
   ```
   Generate a value for `AIRFLOW_FERNET_KEY`:
   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
2. Start the platform (Postgres, MinIO, Airflow, Metabase):
   ```bash
   docker compose up -d --build
   ```
   `airflow-init` runs once to set up the metadata database and admin user;
   give it a minute or two before the webserver reports healthy.
3. Generate a batch of sample data (this is a one-off tool, not started automatically):
   ```bash
   docker compose run --rm data-generator
   ```
4. Open **Airflow** at http://localhost:8080 (login from `.env`). The
   `sales_pipeline` DAG runs every 10 minutes on its own, or trigger it
   immediately:
   ```bash
   docker compose exec airflow-webserver airflow dags trigger sales_pipeline
   ```
5. Open **MinIO** at http://localhost:9001 to see the raw/processed files.
6. Open **Metabase** at http://localhost:3000, complete its first-run setup,
   then add a database connection:
   - Type: PostgreSQL
   - Host: `postgres`
   - Port: `5432`
   - Database: `app_data`
   - Username/Password: from `.env`

   From there, build a dashboard on the `sales_records` table — e.g. revenue
   over time, orders by category — with clear chart titles and labeled axes
   so it reads well for a non-technical audience.

## Running tests and lint locally

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

pytest -q         # unit tests (data generation + cleaning logic, mocked MinIO)
ruff check .       # lint
```

## CI/CD

See `.github/workflows/main.yml`. On every push/PR: lint → unit tests →
Docker image builds → a fast smoke test of Postgres/MinIO/Metabase. The full
end-to-end data-flow check (MinIO → Airflow → Postgres → Metabase) is heavier
to boot, so it runs only on a manual trigger or nightly schedule rather than
on every push.

## Repository structure

```
├── dags/                # Airflow DAG definitions
├── data_generator/      # Synthetic data generator (pure functions + MinIO uploader)
├── transform/           # Pure cleaning/validation functions, shared by the DAG and tests
├── config/               # constants.py, logging setup, Postgres init script, Airflow Dockerfile
├── tests/                # pytest unit tests
├── logs/                 # gitignored — app-level logs (data_generator.log, pipeline.log)
├── docker-compose.yml    # Platform orchestration
├── requirements.txt
├── .env.example
├── .github/workflows/    # CI/CD pipeline
└── README.md
```

## Logs

Application-level logs (separate from Airflow's own task logs) are written
to `logs/data_generator.log` and `logs/pipeline.log`. Every file drop,
upload, skip, or row-drop is logged there for traceability. This directory
is gitignored — existing log files are never deleted or overwritten without
asking first.
