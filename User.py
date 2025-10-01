from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from security import hash_password
from auth import auth_router
from db import get_db
from models import User

app = FastAPI(title="User Management API")

# 🔐 Register auth routes
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

from posts import router as posts_router
app.include_router(posts_router) #uses prefix "/posts" from the router

# -----------------------
# Pydantic Schemas
# -----------------------
class UserIn(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        orm_mode = True  # ✅ allows returning SQLAlchemy models directly


# -----------------------
# Health Check
# -----------------------
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return {"status": "healthy", "users_count": len(users)}


# -----------------------
# Create User
# -----------------------
@app.post("/users", response_model=UserOut, status_code=201)
async def create_user(user: UserIn, db: AsyncSession = Depends(get_db)):
    # check unique username/email
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        full_name=user.full_name,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


# -----------------------
# Get All Users
# -----------------------
@app.get("/users", response_model=List[UserOut])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()


# -----------------------
# Search Users
# -----------------------
@app.get("/users/search", response_model=List[UserOut])
async def search_users(
    username: Optional[str] = None,
    email: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(User)
    if username:
        query = query.where(User.username.ilike(f"%{username}%"))
    if email:
        query = query.where(User.email.ilike(f"%{email}%"))

    result = await db.execute(query)
    return result.scalars().all()


# -----------------------
# Get Specific User
# -----------------------
@app.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# -----------------------
# Update User
# -----------------------
@app.put("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: int, user_updates: UserIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")

    user.username = user_updates.username
    user.email = user_updates.email
    user.full_name = user_updates.full_name
    user.password_hash = hash_password(user_updates.password)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# -----------------------
# Delete User
# -----------------------
@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return {"message": f"User {user.username} deleted successfully"}
