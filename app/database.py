from pymongo import MongoClient
from pymongo.database import Database

from app.config import settings


_client = MongoClient(
    settings.mongodb_uri,
    maxPoolSize=10,
    minPoolSize=1,
    serverSelectionTimeoutMS=5000,
)


def get_database() -> Database:
    return _client[settings.mongodb_database]


def ensure_indexes() -> None:
    db = get_database()
    db.users.create_index("email", unique=True)
    db.logs.create_index([("timestamp", -1)])
    db.courses.create_index("code", unique=True)
    db.documents.create_index("document_id", unique=True)
    db.documents.create_index("course_code")
