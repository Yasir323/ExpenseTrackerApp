from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from starlette import status

from app.config import ExpenseSplitType
from app.models import DbExpense
from app.schema import AddExpensePayload


def get_participants(payload: AddExpensePayload):
    db_participants = []
    match payload.expense_type.upper():
        case ExpenseSplitType.EQUAL:
            for participant in payload.participants:
                db_participant = {
                    "user_id": participant.user_id,
                    "amount": payload.amount / len(payload.participants)
                }
                db_participants.append(db_participant)
        case ExpenseSplitType.EXACT:
            spent = payload.amount
            for participant in payload.participants:
                spent -= participant.contribution
                db_participant = {
                    "user_id": participant.user_id,
                    "amount": participant.contribution
                }
                db_participants.append(db_participant)
            if spent != 0:
                raise ValueError
        case ExpenseSplitType.PERCENT:
            total_perc = 0
            for participant in payload.participants:
                total_perc += participant.contribution
                amount_owed = payload.amount * participant.contribution / 100
                db_participant = {
                    "user_id": participant.user_id,
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


async def add_expense_to_db(db: AsyncIOMotorDatabase, payload: AddExpensePayload):
    try:
        expenses = await expense_adapter(payload)
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
