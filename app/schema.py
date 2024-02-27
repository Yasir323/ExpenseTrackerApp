import datetime
from typing import Optional, TypeVar, List

from pydantic import BaseModel, Field, UUID4, EmailStr

from app.config import ExpenseSplitType, id_factory

Number = TypeVar("Number", float, int)


class Participant(BaseModel):
    user_id: str
    contribution: Optional[Number]


class AddExpensePayload(BaseModel):
    amount: float = Field(ge=0, le=1_00_00_000, description="Amount should be between 0 and 1,00,00,000.")
    payee_id: str
    expense_type: ExpenseSplitType
    name: Optional[str] = Field(max_length=128, default=None)
    notes: Optional[str] = Field(max_length=500, default=None)
    participants: List[Participant]


class User(BaseModel):
    user_id: str
    amount: Number


class ExpenseResponse(BaseModel):
    amount: Number
    date: datetime.datetime
    name: Optional[str]
    notes: Optional[str]
    participants: List[User]


class UserResponse(BaseModel):
    name: str = Field(max_length=128)
    email: EmailStr = Field(max_length=256)
    phone: int


class BalanceResponse(BaseModel):
    user: str
    amount_owed: Number


class Expense(BaseModel):
    borrower: str
    lender: str
    amount: Number
