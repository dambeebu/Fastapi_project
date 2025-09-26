from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = "postgresql+asyncpg://postgres:Ccymefv3.@localhost:5432/backend_bootcamp"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

#Dependency for FastAPI routes
async def get_db():
    async with SessionLocal() as session:
        yield session