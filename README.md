# Web-Based LinkedIn Job Postings Analysis and Management System

A full-stack analytics platform that turns the Kaggle *LinkedIn Job Postings
(2023–2024)* dataset into an interactive, browser-based decision-support tool.
It ships a normalised relational database, a Flask REST API (with an NLP skills
extractor and a machine-learning job classifier) and a Vue.js 3 single-page
application with an ECharts analytics dashboard.

> **Stack:** Flask 3 · SQLAlchemy · MySQL 8 / SQLite · Vue.js 3 · Element Plus ·
> ECharts · pandas · scikit-learn · Docker

## Architecture

A classic three-tier (Browser/Server) architecture:

| Tier | Technology | Responsibility |
|------|------------|----------------|
| Presentation | Vue.js 3 SPA, Element Plus, ECharts | Reactive UI, charts, routing |
| Application | Flask REST API, SQLAlchemy, JWT | Business logic, NLP, ML, auth |
| Data | MySQL 8 (prod) / SQLite (dev) | Normalised 3NF storage |

See `docs/figures/fig_architecture.png` and `docs/figures/fig_er.png`.

## Repository layout

```
system/
  backend/
    app/
      api/         REST blueprints (postings, companies, skills, analytics, auth)
      models/      SQLAlchemy ORM models (3NF)
      services/    nlp.py (skills), classifier.py (ML), analytics.py (aggregations)
      config.py    DATABASE_URL-driven configuration
    etl/import_data.py   Kaggle CSV -> cleaned -> database pipeline
    tests/         pytest unit + API integration suite
    schema.sql     MySQL DDL (production target)
    run.py         dev entry point
  frontend/        Vue 3 + Vite SPA
  docs/figures/    generated charts and diagrams
  docker-compose.yml
```

## Prerequisites

- Python 3.9+
- Node.js 16+
- (Optional) MySQL 8.0 and/or Docker

## Quick start (zero-config, SQLite)

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
python -m etl.import_data            # build & populate data/app.db (one-off)
python run.py                        # serves http://127.0.0.1:5000

# 2. Frontend (separate terminal)
cd frontend
npm install
npm run dev                          # serves http://127.0.0.1:5173 (proxies /api)
```

Default seeded accounts: `admin / admin123` (admin) and `demo / demo123` (user).

## Running against MySQL (production target)

The application is database-agnostic: the same ORM models and pipeline run
against either backend, selected purely through the `DATABASE_URL` environment
variable. Create a `backend/.env` (see `backend/.env.example`) containing, e.g.:

```
DATABASE_URL=mysql+pymysql://root:<password>@127.0.0.1:3306/linkedin_jobs?charset=utf8mb4
```

Then populate MySQL. The fastest route reuses the already-cleaned development
data and applies `schema.sql` (indexes, foreign keys and a FULLTEXT index):

```bash
cd backend
python -m etl.migrate_to_mysql      # apply schema.sql + bulk-copy SQLite -> MySQL
python run.py                        # now serving from MySQL
```

Alternatively, load directly from the raw CSVs into MySQL:

```bash
mysql -u root -p < backend/schema.sql
export DATABASE_URL="mysql+pymysql://root:<password>@127.0.0.1:3306/linkedin_jobs?charset=utf8mb4"
cd backend && python -m etl.import_data
```

> The system has been deployed and benchmarked end-to-end on MySQL 5.7.44.

## Performance optimisations

- **Analytics cache** (`app/services/cache.py`): a thread-safe TTL cache wraps
  the dataset-wide aggregations, taking the Dashboard/salary/skills endpoints
  from 1–3 s (cold) to sub-millisecond once warmed. Disabled automatically under
  test for isolation.
- **Relevance-ranked FULLTEXT search**: on MySQL, keyword search uses the
  `MATCH … AGAINST` FULLTEXT index ranked by relevance, cutting a broad query
  from ~2.5 s to ~30 ms. SQLite falls back to a portable `LIKE` scan.

## One-command deployment (Docker)

```bash
docker compose up --build
# frontend  -> http://localhost:8080
# backend   -> http://localhost:5000
# mysql     -> localhost:3306 (schema auto-applied)
```

Then run the ETL once inside the backend container to populate MySQL.

## Testing

```bash
cd backend
python -m pytest -v        # 34 unit + integration tests
```

## Key API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/postings` | Paginated list with search/filter/sort |
| GET | `/api/postings/<id>` | Posting detail (skills + company) |
| GET | `/api/postings/<id>/similar` | Similar postings by category |
| GET | `/api/companies` | Company directory |
| GET | `/api/companies/<id>` | Company detail + recent postings |
| GET | `/api/skills` | Skill demand ranking |
| GET | `/api/skills/cooccurrence` | Skill co-occurrence matrix |
| POST | `/api/skills/extract` | NLP skill extraction from text |
| GET | `/api/analytics/dashboard` | Aggregated dashboard metrics |
| GET | `/api/analytics/salary` | Salary distribution & by-category |
| POST | `/api/analytics/classify` | ML job-category prediction |
| POST | `/api/auth/login` · `/register` · `GET /me` | JWT authentication |

## Regenerating report figures

```bash
cd docs/_gen
python gen_data.py        # data charts from the live database
python gen_diagrams.py    # architecture / ER / use-case / Gantt
python perf.py            # API performance benchmark
```

## License

Academic project (UEL CN6000). Dataset © its respective authors on Kaggle.
