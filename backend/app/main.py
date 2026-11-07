from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from sqlalchemy import text

from app.db.session import engine

app = FastAPI(
    title="ReAnalyze API",
    description="Backend for the AI Research Analyst",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ReAnalyze API",
    }

@app.get("/api/v1/health/db")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        ) from e


@app.get("/api/v1")
def root():
    return {
        "message": "Welcome to ReAnalyze API",
    }