from fastapi import FastAPI
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app.routes import dashboard, goals, transactions

app = FastAPI(
    title="KTeensApp",
    summary="Piwulang Becik Teens Club application powered and supported by Kanaede.",
    description="KTeensApp API for private community built by Kanaede to support Piwulang Becik that also known as PBx.",
    version="0.0.1 alpha"
)

# app.frontend("/", directory="dist", fallback="index.html")

app.include_router(transactions.router)
app.include_router(goals.router)
app.include_router(dashboard.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

jobstores = {
    'default': SQLAlchemyJobStore
}