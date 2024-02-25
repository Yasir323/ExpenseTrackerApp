from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn

from app.database import DatabaseConnectionManager
from app.routes.expense import expense_router
from app.routes.user import user_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
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

    # Clean up the ML models and release the resources
    DatabaseConnectionManager().close_conn()


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(expense_router)

if __name__ == "__main__":
    uvicorn.run(app=app, host="127.0.0.1", port=8000)
