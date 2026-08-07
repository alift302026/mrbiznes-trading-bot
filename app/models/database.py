from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "trading_assistant.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


Base = declarative_base()