from fastapi import FastAPI

from app.routes import dashboard, goals, transactions

app = FastAPI()

app.include_router(transactions.router)
app.include_router(goals.router)
app.include_router(dashboard.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}