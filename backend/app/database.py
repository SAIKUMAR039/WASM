from pymongo import MongoClient
from app.config import settings

class MongoDB:
    client: MongoClient = None
    db = None

mongo = MongoDB()

def connect_to_mongo():
    """Establish connection to MongoDB using the configured URL."""
    try:
        mongo.client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=3000)
        
        # Get database from connection URI or config default
        db_name = settings.MONGODB_DB_NAME
        try:
            parsed_db = mongo.client.get_default_database().name
            if parsed_db:
                db_name = parsed_db
        except Exception:
            pass

        mongo.db = mongo.client[db_name]
        # Ping check
        mongo.client.admin.command('ping')
        print(f"[WasmBox] Successfully connected to MongoDB at {settings.MONGODB_URL} (db: '{db_name}')")
    except Exception as err:
        print(f"[WasmBox] MongoDB connection warning for '{settings.MONGODB_URL}': {err}")
        print("[WasmBox] In-memory fallback mode activated.")
        mongo.client = None
        mongo.db = None

def close_mongo_connection():
    """Close MongoDB connection gracefully."""
    if mongo.client:
        mongo.client.close()
        print("[WasmBox] MongoDB connection closed.")

def get_db():
    """Dependency helper returning active MongoDB database instance."""
    return mongo.db
