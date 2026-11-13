import threading

from fastapi import FastAPI
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from fastapi.staticfiles import StaticFiles

from app import templates
from app.function.donation_services import schedule_update_goal
from app.function.frontend import rupiah
from app.services.handlers import register_exception_handlers
from app.routers import admin, goal, transactions, users

app = FastAPI(
    title="KTeensApp",
    summary="Piwulang Becik Teens Club application powered and supported by Kanaede.",
    description="KTeensApp API for private community built by Kanaede to support Piwulang Becik that also known as PBx.",
    version="0.0.1 alpha"
)

# Redirect the main path
# app.frontend("/", directory="dist", fallback="index.html")

register_exception_handlers(app)

app.include_router(admin.router)
app.include_router(goal.router)
app.include_router(transactions.router)
app.include_router(users.router)
app.include_router(users.router_notification)

templates.env.filters["rupiah"] = rupiah

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

jobstores = {
    'default': SQLAlchemyJobStore
}

goal_updater = threading.Thread(target=schedule_update_goal, args=(60,))

goal_updater.start()