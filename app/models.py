import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat, EmailStr, FilePath

from app.config import id_factory


class DbUser(BaseModel):
    model_config = ConfigDict(populate_by_name=False)

    id: str = Field(default_factory=id_factory, alias="_id")
    name: str = Field(max_length=128)
    email: EmailStr = Field(max_length=256)
    phone: int


class DbParticipant(BaseModel):
    user_id: str = Field(max_length=128)
    amount: NonNegativeFloat = Field(le=1_00_00_000)


class DbExpense(BaseModel):
    model_config = ConfigDict(populate_by_name=False)

    id: str = Field(default_factory=id_factory, alias="_id")
    payee_id: str
    amount: NonNegativeFloat = Field(le=1_00_00_000)
    date: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    name: Optional[str] = Field(max_length=128)
    notes: Optional[str] = Field(max_length=500)
    images: Optional[List[FilePath]]
    participants: List[DbParticipant]
