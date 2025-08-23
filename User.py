from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, validator
from typing import List
from security import hash_password
from auth import auth_router

app = FastAPI(title= "User Management API")

app.include_router(auth_router, prefix="/auth", tags=["authentication"])

users_db = []

class UserIn(BaseModel):
    username : str
    email: EmailStr
    password: str
    full_name: str | None = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        
        return v

class UserOut(BaseModel):
    id : int
    username : str
    email: EmailStr
    full_name: str | None = None


@app.get("/health")
def health_check():
    return {"status" : "healthy", "users_count" : len(users_db)}

#create user
@app.post("/users", response_model = UserOut, status_code= 201)
def create_user(user: UserIn):
    for existing_user in users_db:
        if existing_user["username"] == user.username:
            raise HTTPException(status_code = 400, detail = "Username already exists")
        
    new_user = {
        "id" : len(users_db) + 1,
        "username" : user.username,
        "email" : user.email,
        "password_hash": hash_password(user.password),
        "full_name" : user.full_name
    }

    users_db.append(new_user)
    return {
        "id" : new_user["id"],
        "username" : new_user["username"],
        "email" : new_user["email"],
        "full_name" : new_user["full_name"]
    }

#get all users
@app.get("/users", response_model= List[UserOut])
def get_users():
    return users_db

#search users
@app.get("/users/search", response_model=List[UserOut])
def search_users(username: str = None, email: str = None):
    results = []
    for user in users_db:
        if (
            (username is None or username.lower() in user["username"].lower())
            and
            (email is None or email.lower() in user["email"].lower())
        ):
            results.append(user)
    return results

#specific user
@app.get("/users/{user_id}", response_model = UserOut)
def get_user(user_id: int):
    for user in users_db:
        if user["id"] == user_id:
            return user
        
    raise HTTPException(status_code= 404, detail = "User not found")

#update user
@app.put("/users/{user_id}", response_model = UserOut)
def update_user(user_id: int, user_updates: UserIn):
    for user in users_db:
        if user["id"] == user_id:
            user["username"] = user_updates.username
            user["email"] = user_updates.email
            user["full_name"] = user_updates.full_name
            return user
    raise HTTPException(status_code=404, detail="User does not exist")

#delete user

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    for i, user in enumerate(users_db):
        if user["id"] == user_id:
            deleted_user = users_db.pop(i)
            return {"message" : f"User {deleted_user['username']} deleted successfully"}
        
    raise HTTPException(status_code = 404, detail = "User not found")


@app.get("/debug/users")
def debug_users():
    return {"users_db": users_db}