from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn

from app.database import DatabaseConnectionManager
from app.routes.expense import expense_router
from app.routes.user import user_router
from app.scheduler import send_weekly_summary

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the db
    db = DatabaseConnectionManager().get_db
    users_col = db.get_collection("users")
    await users_col.create_index({"name": 1}, unique=True)
    await users_col.create_index({"email": 1}, unique=True)
    await users_col.create_index({"phone": 1}, unique=True)
    transactions_col = db.get_collection("transactions")
    await transactions_col.create_index({"payee_id": 1})
    await transactions_col.create_index({"payer_id": 1})
    print("Indexes created!")

    yield

    # Clean up the connections and release the resources
    DatabaseConnectionManager().close_conn()


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(expense_router)

# Configure scheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(send_weekly_summary, "interval", weeks=1)  # Run weekly
scheduler.start()

if __name__ == "__main__":
    uvicorn.run(app=app, host="127.0.0.1", port=8000)
