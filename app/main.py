import threading

from fastapi import FastAPI
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app.routes import cookie, goals, transactions, user
from app.services import goal_service

app = FastAPI(
    title="KTeensApp",
    summary="Piwulang Becik Teens Club application powered and supported by Kanaede.",
    description="KTeensApp API for private community built by Kanaede to support Piwulang Becik that also known as PBx.",
    version="0.0.1 alpha"
)

# Redirect the main path
# app.frontend("/", directory="dist", fallback="index.html")

app.include_router(transactions.router)
app.include_router(goals.router)
app.include_router(user.router)
app.include_router(cookie.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

jobstores = {
    'default': SQLAlchemyJobStore
}

goal_updater = threading.Thread(target=goal_service.schedule_update_goal, args=(60,))

goal_updater.start()