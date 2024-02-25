from typing import List

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from starlette import status

from app.config import ExpenseSplitType
from app.database import get_db
from app.models import DbExpense
from app.schema import AddExpensePayload


def split_amount(total_amount: float, num_people: int) -> List[float]:
    equal_share = total_amount / num_people
    remainder = total_amount - (equal_share * num_people)

    # Distribute equal share among all participants
    amounts = [round(equal_share, 2) for _ in range(num_people)]

    # Distribute remainder fairly among participants
    for i in range(int(remainder * 100)):  # Multiply by 100 to avoid floating-point precision issues
        amounts[i % num_people] += 0.01

    return amounts


def get_participants_by_splitting_amount_equally(total_amount, participants) -> List[dict]:
    db_participants = []
    amounts = split_amount(total_amount=total_amount, num_people=len(participants))
    for index, participant in enumerate(participants):
        db_participant = {
            "user_id": participant.user_id,
            "amount": amounts[index]
        }
        db_participants.append(db_participant)
    return db_participants


def get_participants_by_splitting_amount_exactly(total_amount, participants) -> List[dict]:
    spent = total_amount
    db_participants = []
    for participant in participants:
        spent -= participant.contribution
        db_participant = {
            "user_id": participant.user_id,
            "amount": participant.contribution
        }
        db_participants.append(db_participant)
    if spent != 0:
        raise ValueError
    return db_participants


def get_participants_by_splitting_amount_by_percentage(total_amount, participants) -> List[dict]:
    total_perc = 0
    db_participants = []
    for participant in participants:
        total_perc += participant.contribution
        amount_owed = total_amount * participant.contribution / 100
        db_participant = {
            "user_id": participant.user_id,
            "amount": amount_owed
        }
        db_participants.append(db_participant)
    if total_perc > 100:
        raise ValueError
    return db_participants


def get_participants_by_splitting_amount_by_weight(total_amount, participants) -> List[dict]:
    total_weight = sum([p.contribution for p in participants])
    db_participants = []
    for participant in participants:
        amount_owed = total_amount * participant.contribution / total_weight
        db_participant = {
            "user_id": participant.user_id,
            "amount": amount_owed
        }
        db_participants.append(db_participant)
    return db_participants


def get_participants(payload: AddExpensePayload):
    match payload.expense_type.upper():
        case ExpenseSplitType.EQUAL:
            db_participants = get_participants_by_splitting_amount_equally(payload.amount, payload.participants)
        case ExpenseSplitType.EXACT:
            db_participants = get_participants_by_splitting_amount_exactly(payload.amount, payload.participants)
        case ExpenseSplitType.PERCENT:
            db_participants = get_participants_by_splitting_amount_by_percentage(payload.amount, payload.participants)
        case ExpenseSplitType.WEIGHT:
            db_participants = get_participants_by_splitting_amount_by_weight(payload.amount, payload.participants)
        case _:
            db_participants = []
    return db_participants


async def expense_adapter(payload: AddExpensePayload) -> DbExpense:
    db_expense = DbExpense(
        payee_id=payload.payee_id,
        amount=payload.amount,
        name=payload.name,
        notes=payload.notes,
        images=None,
        participants=get_participants(payload)
    )
    return db_expense


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


async def add_expense_to_db(db: AsyncIOMotorDatabase, expenses: DbExpense):
    try:
        print(expenses.dict(by_alias=True))
        await db["expenses"].insert_one(expenses.dict(by_alias=True))
        await update_transactions(db, expenses)
        return expenses.id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid total contribution."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add expense: {str(e)}"
        )


async def get_user_balance(db: AsyncIOMotorDatabase, user_id: str):
    pipeline = [
        {"$match": {"payer_id": user_id}},
        {"$group": {"_id": "$payee_id", "amount_owed": {"$sum": "$amount"}}},
        {"$sort": {"amount_owed": 1}}
    ]
    result = [txn async for txn in db["transactions"].aggregate(pipeline)]
    user_name_map = await get_username([txn["_id"] for txn in result])
    print(user_name_map)
    balance = [{"user": user_name_map[txn["_id"]], "amount_owed": txn["amount_owed"]} for txn in result]
    return balance


async def get_username(user_idx: List[str] = None):
    db = get_db()
    col = db.get_collection("users")
    if user_idx:
        query = {"_id": {"$in": user_idx}}
    else:
        query = {}
    projection = {"_id": 1, "name": 1}
    user_email_map = {}
    async for doc in col.find(query, projection):
        user_email_map[doc["_id"]] = doc["name"]
    return user_email_map


async def get_emails(user_idx: List[str] = None):
    db = get_db()
    col = db.get_collection("users")
    if user_idx:
        query = {"_id": {"$in": user_idx}}
    else:
        query = {}
    projection = {"_id": 1, "email": 1}
    user_email_map = {}
    async for doc in col.find(query, projection):
        user_email_map[doc["_id"]] = doc["email"]
    return user_email_map
