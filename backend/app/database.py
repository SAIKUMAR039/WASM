from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# SQLAlchemy setup (for SQLite fallback/migration)
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# MongoDB Client Setup
class MongoDatabase:
    client = None
    db = None

mongo_db = MongoDatabase()

def init_mongo_db():
    """Initializes MongoDB client connection or returns fallback."""
    try:
        from pymongo import MongoClient
        mongo_db.client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        mongo_db.db = mongo_db.client[settings.MONGODB_DB_NAME]
        # Quick ping test
        mongo_db.client.admin.command('ping')
        print(f"Connected to MongoDB at {settings.MONGODB_URL} ({settings.MONGODB_DB_NAME})")
    except Exception as e:
        print(f"MongoDB connection notice: {e}. Falling back to SQLite/In-Memory mode.")
        mongo_db.client = None
        mongo_db.db = None

def get_mongo_db():
    """Dependency helper to return active MongoDB instance."""
    return mongo_db.db
