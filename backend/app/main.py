from fastapi import FastAPI
from sqlalchemy import text

from app.db.session import engine
from app.routers import auth, document


app = FastAPI(
    title="Healthcare Document Intelligence API",
    version="1.0.0",
)


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/v1/health/db")
def database_health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"database": "ok"}


app.include_router(
    auth.router,
    prefix="/api/v1",
)

app.include_router(
    document.router,
    prefix="/api/v1",
)