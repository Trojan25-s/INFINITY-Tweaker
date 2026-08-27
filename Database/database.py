"""
Database connection and connection pooling for scalable multi-user backend.
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "infinity_license.db")
DATABASE_URL = os.getenv("INFINITY_DATABASE_URL", f"sqlite:///{DB_PATH}")

# Connection configuration with pooling for high multi-user concurrency
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True
    )
    
    # Enable WAL mode for high concurrent read/write performance in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=25,
        max_overflow=50,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
