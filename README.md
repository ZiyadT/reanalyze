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