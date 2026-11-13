# ReAnalyze

Personal AI Research Analyst.

## Tech Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: Python, FastAPI
- Database: PostgreSQL 16, pgvector
- ORM: SQLAlchemy
- Infrastructure: Docker Compose

## Project Structure

```text
reanalyze/
├── frontend/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── services/
│   │   └── main.py
│   ├── requirements.txt
│   └── .venv/
├── docker-compose.yml
├── .env
├── .env.example
└── README.md
```

## Backend models

SQLAlchemy models share the declarative base in `backend/app/db/base.py`.
Add models in `backend/app/db/models.py` and import them before using
`Base.metadata`, so their tables are registered. Embedding configurations are
immutable: create a new row instead of changing an existing one. The database
enforces this rule even for direct SQL updates.

## Database migrations

Start PostgreSQL with `docker compose up -d db`, set `DATABASE_URL` (or add it
to the root `.env`), and install `backend/requirements.txt` in the backend
virtual environment. Use the `postgresql+psycopg` URL scheme with the
installed psycopg driver. From `backend/`:

```bash
alembic upgrade head
alembic current
```

Create future migrations with `alembic revision --autogenerate -m "description"`
and review them before applying; Alembic does not autogenerate trigger changes.
The current migrations create embedding configurations, users, workspaces,
documents, workspace-document membership, document chunks, chunk embeddings,
and saved reports.
The workspace migration also uses a database trigger to remove current
document links when a workspace is archived; Alembic will not generate that
trigger automatically.

To run the PostgreSQL migration and constraint tests, set `TEST_DATABASE_URL`
to a PostgreSQL database on which the test user can create schemas, then run
from `backend/`:

```bash
python -m unittest discover -s tests -v
```

The tests create and remove an isolated, uniquely named schema. They skip if
`TEST_DATABASE_URL` is unset. `alembic downgrade base` removes all migrated
tables and their data; use it only on a disposable development database.