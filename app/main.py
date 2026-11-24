import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import templates
from app.function.donation_services import schedule_update_goal
from app.function.frontend import rupiah
from app.services.handlers import register_exception_handlers
from app.routers import admin, application, goal, pages, transactions, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = asyncio.Event()
    updater_task = asyncio.create_task(schedule_update_goal(60, stop_event))
    try:
        yield
    finally:
        stop_event.set()
        await updater_task


app = FastAPI(
    title="KTeensApp",
    summary="Piwulang Becik Teens Club application powered and supported by Kanaede.",
    description="KTeensApp API for private community built by Kanaede to support Piwulang Becik TeensClub that also known as PBx Teens Club.",
    version="0.0.1 alpha",
    lifespan=lifespan,
)

# Redirect the main path
app.frontend("/", directory="dist/", fallback="404.html")

register_exception_handlers(app)

app.include_router(application.router)
app.include_router(admin.router)
app.include_router(goal.router)
app.include_router(transactions.router)
app.include_router(users.router_user)
app.include_router(users.router_notification)
app.include_router(pages.router)

templates.env.filters["rupiah"] = rupiah

app.mount(
    "/static",
    StaticFiles(directory="app/frontend/static"),
    name="static",
)

# @app.get("/")
# async def root():
#     return {"message": "Hello Bigger Applications!"}
