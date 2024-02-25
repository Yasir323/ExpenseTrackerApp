import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


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


def get_db() -> AsyncIOMotorDatabase:
    db_manager = DatabaseConnectionManager()
    return db_manager.get_db
