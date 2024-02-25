from typing import List

import pymongo
from fastapi import Depends, APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from starlette import status

from app.crud import get_user_balance
from app.database import get_db
from app.models import DbUser
from app.schema import UserResponse, BalanceResponse

user_router = APIRouter(prefix="/users")


@user_router.get("/", response_model=List[DbUser])
async def get_users(db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        users = [user async for user in db["users"].find()]
        if not users:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return users
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        query = {"_id": user_id}
        projection = {"_id": 0}
        user = await db["users"].find_one(query, projection)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return user


@user_router.post("/")
async def add_user(payload: UserResponse, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        user = DbUser(**payload.dict())
        print(user.id)
        user_db = await db["users"].insert_one(user.dict(by_alias=True))
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username, email or phone already registered."
        )
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return {"user_created": str(user_db.inserted_id)}


@user_router.get("/balance/{user_id}", response_model=List[BalanceResponse])
async def get_balances(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        result = await get_user_balance(db, user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return result
