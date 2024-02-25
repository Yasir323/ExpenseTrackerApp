from typing import List

from fastapi import HTTPException, APIRouter, Depends, UploadFile, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from starlette import status

from app.config import float_scale
from app.crud import add_expense_to_db, expense_adapter
from app.database import get_db
from app.file_io import store_files
from app.notification import send_expense_notification
from app.schema import ExpenseResponse, AddExpensePayload

expense_router = APIRouter(prefix="/expenses")


@expense_router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(expense_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        # Retrieve expense by ID
        query = {"_id": expense_id}
        projection = {
            "_id": 0,
            "amount": 1,
            "date": 1,
            "name": 1,
            "notes": 1,
            "participants": 1
        }
        expense = await db["expenses"].find_one(query, projection)
        if expense is None:
            raise HTTPException(status_code=404, detail="Expense not found")
        return expense
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch expense: {str(e)}")


@expense_router.post("/")
async def add_expense(payload: AddExpensePayload,
                      background_tasks: BackgroundTasks,
                      db: AsyncIOMotorDatabase = Depends(get_db)):
    # out_file_paths = None
    # if images:
    #     out_file_paths = await store_files(images)   # On disk or cloud
    # participants_ = [Participant(user_id=k, contribution=v) for k, v in participants.items()]
    payload = AddExpensePayload(
        amount=payload.amount,
        payee_id=payload.payee_id,
        expense_type=payload.expense_type.upper(),
        name=payload.name,
        notes=payload.notes,
        participants=payload.participants
    )
    expenses = await expense_adapter(payload)
    background_tasks.add_task(send_expense_notification, expenses)
    expense_id = await add_expense_to_db(db, expenses)
    return {"expenseId": expense_id, "message": "Expense added successfully"}


@expense_router.patch("/upload_image/{expense_id}")
async def upload_image(expense_id: str, files: List[UploadFile], db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        file_paths = await store_files(files)
        db["expenses"].update_one({"_id": expense_id}, {"$set": {"images": file_paths}})
    except Exception as err:
        raise err


@expense_router.get("/user/{user_id}", response_model=List[ExpenseResponse])
async def get_expenses_of_user(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        # Retrieve expense by ID
        query = {"$or": [{"payee_id": user_id}, {"participants.user_id": user_id}]}
        result = []
        async for expense in db["expenses"].find(query):
            result.append(expense)

        for r in result:
            r["amount"] = float_scale(r["amount"])
            for p in r["participants"]:
                p["amount"] = float_scale(p["amount"])

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch expense: {str(e)}"
        )
