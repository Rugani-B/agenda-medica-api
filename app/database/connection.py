# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL and "charset=" not in DATABASE_URL:
    sep = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL += f"{sep}charset=utf8mb4"

engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=240,    # renova conexões a cada 4 min (Railway fecha após ~5 min idle)
)

SessionLocal = sessionmaker(
    autocommit  = False,
    autoflush   = False,
    bind        = engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
