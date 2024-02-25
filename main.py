import datetime
from contextlib import asynccontextmanager
from enum import Enum, unique
import os
from typing import List, Optional, TypeVar, Dict
import uuid

import aiofiles
import bson
import pymongo.errors
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, Depends, UploadFile, HTTPException, Form, File
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel, Field, EmailStr, NonNegativeFloat, UUID4, FilePath, ConfigDict, ValidationError, \
    validator, field_validator
from starlette import status

load_dotenv()


class DatabaseConnectionManager:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # cls._instance.client = AsyncIOMotorClient(os.environ.get("DB_URI"))
            # cls._instance.db = cls._instance.client[os.environ.get("DB_NAME")]
        return cls._instance

    def __init__(self):
        self.client = AsyncIOMotorClient(os.environ.get("DB_URI"), uuidRepresentation="standard")
        self.db = self.client[os.environ.get("DB_NAME")]

    @property
    def get_db(self):
        return self.db

    def close_conn(self):
        self.client.close()


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

expense_router = APIRouter(prefix="/expenses")

Number = TypeVar("Number", float, int)


def float_scale(x: float) -> str:
    return f"{x:.2f}"


@unique
class ExpenseSplitType(str, Enum):
    EQUAL = "EQUAL"
    EXACT = "EXACT"
    PERCENT = "PERCENT"


# @app.on_event("startup")
# async def start_db_client():
#     DatabaseConnectionManager()
#     print("Connected to Database")
#
#
# @app.on_event("shutdown")
# async def shutdown_db_client():
#     DatabaseConnectionManager().close_conn()

def get_db() -> AsyncIOMotorDatabase:
    db_manager = DatabaseConnectionManager()
    return db_manager.get_db


# Database Models
# class DbBalance(BaseModel):
#     user_id: UUID4
#     balance: NonNegativeFloat = Field(decimal_places=2)


class DbUser(BaseModel):
    model_config = ConfigDict(populate_by_name=False)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    name: str = Field(max_length=128)
    email: EmailStr = Field(max_length=256)
    phone: int
    # balances: List[DbBalance]


class DbParticipant(BaseModel):
    user_id: str = Field(max_length=128)
    amount: NonNegativeFloat = Field(le=1_00_00_000)


class DbExpense(BaseModel):
    model_config = ConfigDict(populate_by_name=False)

    id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
    payee_id: str
    amount: NonNegativeFloat = Field(le=1_00_00_000)
    date: datetime.datetime = Field(default=datetime.datetime.utcnow())
    name: Optional[str] = Field(max_length=128)
    notes: Optional[str] = Field(max_length=500)
    images: Optional[List[FilePath]]
    participants: List[DbParticipant]


################################################################################
class Participant(BaseModel):
    user_id: str
    contribution: Optional[Number]


class AddExpensePayload(BaseModel):
    amount: float = Field(ge=0, le=1_00_00_000, description="Amount should be between 0 and 1,00,00,000.")
    payee_id: str
    expense_type: ExpenseSplitType
    name: Optional[str] = Field(max_length=128, default=None)
    notes: Optional[str] = Field(max_length=500, default=None)
    images: Optional[List[UploadFile]] = None
    participants: List[Participant]


class User(BaseModel):
    user_id: UUID4
    amount: str


class ExpenseResponse(BaseModel):
    amount: str
    date: datetime.datetime
    name: Optional[str]
    notes: Optional[str]
    participants: List[User]


class GetUserPayload(BaseModel):
    name: str = Field(max_length=128)
    email: EmailStr = Field(max_length=256)
    phone: int


class UserResponse(BaseModel):
    name: str = Field(max_length=128)
    email: EmailStr = Field(max_length=256)
    phone: int


async def store_files(images):
    paths = []
    for image in images:
        out_file_path = os.path.join(os.getcwd(), "resources", image.filename)
        async with aiofiles.open(out_file_path, 'wb') as out_file:
            content = await image.read()
            await out_file.write(content)
        paths.append(out_file_path)
    return ",".join(paths)


def get_participants(payload):
    db_participants = []
    match payload.expense_type.upper():
        case ExpenseSplitType.EQUAL:
            for participant in payload.participants:
                db_participant = {
                    "user_id": participant["user_id"],
                    "amount": payload.amount / len(payload.participants)
                }
                db_participants.append(db_participant)
        case ExpenseSplitType.EXACT:
            total_amt = 0
            for participant in payload.participants:
                total_amt += participant["contribution"]
                db_participant = participant
                db_participants.append(db_participant)
            if total_amt > payload.amount:
                raise ValueError
        case ExpenseSplitType.PERCENT:
            total_perc = 0
            for participant in payload.participants:
                total_perc += participant["contribution"]
                amount_owed = payload.amount * participant["contribution"] / 100
                db_participant = {
                    "user_id": participant["user_id"],
                    "amount": amount_owed
                }
                db_participants.append(db_participant)
            if total_perc > 100:
                raise ValueError
    return db_participants


async def expense_adapter(payload: AddExpensePayload) -> DbExpense:
    db_expense = DbExpense(
        payee_id=payload.payee_id,
        amount=payload.amount,
        name=payload.name,
        notes=payload.notes,
        images=payload.images,
        participants=get_participants(payload)
    )
    return db_expense


async def get_balances(db: AsyncIOMotorDatabase, user_id: UUID4):
    pipeline = [
        {"$match": {"payer_id": user_id}},
        {"$group": {"_id": "payee_id", "amount_owed": {"$sum": "amount"}}},
        {"$sort": {"amount_owed": 1}}
    ]
    return list(await db["transactions"].aggregate(pipeline))


async def update_transactions(db: AsyncIOMotorDatabase, expense: DbExpense):
    payee = expense.payee_id
    docs = []
    for participant in expense.participants:
        if payee != participant.user_id:
            docs.extend([
                {
                    "payee_id": payee,
                    "payer_id": participant.user_id,
                    "amount": participant.amount
                },
                {
                    "payee_id": participant.user_id,
                    "payer_id": payee,
                    "amount": -participant.amount
                }
            ])
    await db["transactions"].insert_many(docs)


async def add_expense_to_db(db: AsyncIOMotorDatabase, payload: AddExpensePayload):
    try:
        expenses = await expense_adapter(payload)
        await db["expenses"].insert_one(**expenses.dict(by_alias=True))
        await update_transactions(db, expenses)
        return expenses.id
    except ValueError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid total contribution.")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add expense: {str(e)}")
    finally:
        await db.close()


@expense_router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(expense_id: UUID4, db: AsyncIOMotorDatabase = Depends(get_db)):
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
        expense = await db["expenses"].get_one(query, projection)
        if expense is None:
            raise HTTPException(status_code=404, detail="Expense not found")
        return expense
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch expense: {str(e)}")


class Checker:
    def __init__(self, model: BaseModel):
        self.model = model

    def __call__(self, data: str = Form(...)):
        try:
            return self.model.model_validate_json(data)
        except ValidationError as e:
            raise HTTPException(
                detail=jsonable_encoder(e.errors()),
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )


@expense_router.post("/")
async def add_expense(amount: NonNegativeFloat = Form(le=1_00_00_000),
                      payee_id: UUID4 = Form(...),
                      expense_type: ExpenseSplitType = Form(...),
                      name: Optional[str] = Form(max_length=128, default=None),
                      notes: Optional[str] = Form(max_length=500, default=None),
                      participants: List[Participant] = Form(...),
                      # payload: AddExpensePayload = Depends(Checker(AddExpensePayload)),
                      images: List[UploadFile] = File(default=None),
                      db: AsyncIOMotorDatabase = Depends(get_db)):
    out_file_paths = None
    if images:
        out_file_paths = await store_files(images)   # On disk or cloud
    # participants_ = [Participant(user_id=k, contribution=v) for k, v in participants.items()]
    payload = AddExpensePayload(
        amount=amount,
        payee_id=payee_id,
        expense_type=expense_type.upper(),
        name=name,
        notes=notes,
        images=out_file_paths,
        participants=participants
    )
    expense_id = await add_expense_to_db(db, payload)
    return {"expenseId": expense_id, "message": "Expense added successfully"}


# @expense_router.post("/")
# async def add_expense(payload: AddExpensePayload, db: AsyncIOMotorDatabase = Depends(get_db)):
#     expense_id = await add_expense_to_db(db, payload)
#     return {"expenseId": expense_id, "message": "Expense added successfully"}


@expense_router.put("/{expense_id}")
async def update_expense(expense_id: UUID4):
    raise HTTPException(404, detail="Unimplemented")


@expense_router.get("/user/{user_id}", response_model=List[ExpenseResponse])
async def get_expenses_of_user(user_id: UUID4, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        # Retrieve expense by ID
        query = {"payee_id": user_id}
        projection = {
            "_id": 0,
            "date": 1,
            "amount": 1,
            "name": 1,
            "notes": 1,
            "participants": 1
        }
        result = list(await db["expenses"].find(query, projection))
        for r in result:
            r["amount"] = float_scale(r["amount"])
            for p in r["participants"]:
                p["amount"] = float_scale(p["amount"])
        if result is None:
            raise HTTPException(status_code=404, detail="Expense not found")
        # user_expenses = []
        # for expense in result:
        #     participants = [User(user_name=participant.name, amount=participant.amount)
        #                     for participant in expense.participants]
        #     expense_response = ExpenseResponse(
        #         amount=expense.amount,
        #         name=expense.name,
        #         date=expense.date,
        #         notes=expense.notes,
        #         participants=participants
        #     )
        #     user_expenses.append(expense_response)
        # return user_expenses
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch expense: {str(e)}")


user_router = APIRouter(prefix="/users")


@user_router.get("/", response_model=List[DbUser])
async def get_users(db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        users = [user async for user in db["users"].find()]
        if not users:
            raise HTTPException(status_code=404)
        return users
    except Exception as err:
        raise err
        # raise HTTPException(status_code=500)


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID4, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        query = {"_id": user_id}
        projection = {"_id": 0}
        user = await db["users"].find_one(query, projection)
        if not user:
            raise HTTPException(status_code=404)
    except:
        raise HTTPException(status_code=500)
    return user


@user_router.post("/")
async def add_user(payload: GetUserPayload, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        user = DbUser(**payload.dict())
        print(user.id)
        user_db = await db["users"].insert_one(user.dict(by_alias=True))
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Username, email or phone already registered.")
    except Exception as err:
        raise err
        # raise HTTPException(status_code=500)
    return {"user_created": str(user_db.inserted_id)}

# @user_router.patch("/{user_id}")
# async def update_user(user_id: int):
#     return {"message": "Update a user"}


app.include_router(user_router)
app.include_router(expense_router)

if __name__ == "__main__":
    uvicorn.run(app=app, host="127.0.0.1", port=8000)
