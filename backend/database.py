from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


DATABASE_URL = "sqlite:///chi.db"


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import models here to ensure they are registered before create_all
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


