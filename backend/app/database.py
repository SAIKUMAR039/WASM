import sys
from pymongo import MongoClient
from app.config import settings

class MongoDB:
    client: MongoClient = None
    db = None

mongo = MongoDB()

def connect_to_mongo():
    """Establish connection to MongoDB cluster/instance."""
    try:
        mongo.client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        mongo.db = mongo.client[settings.MONGODB_DB_NAME]
        # Verify connection
        mongo.client.admin.command('ping')
        print(f"[WasmBox] Successfully connected to MongoDB at {settings.MONGODB_URL} (db: {settings.MONGODB_DB_NAME})")
    except Exception as err:
        print(f"[WasmBox] MongoDB connection warning: {err}. System will initialize fallback memory collections.")
        mongo.client = None
        mongo.db = None

def close_mongo_connection():
    """Close MongoDB connection gracefully."""
    if mongo.client:
        mongo.client.close()
        print("[WasmBox] MongoDB connection closed.")

def get_db():
    """Dependency helper returning MongoDB database instance."""
    return mongo.db
