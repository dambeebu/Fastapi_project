from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List

app = FastAPI(title = "User Management API")

#Our database
users_db = []

#Data Models (contracts)
class UserIn(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

class UserOut(BaseModel):
    id : int
    username : str
    full_name: str | None = None

#Endpoint Health Check
@app.get("/health")
def health_check():
    return{ "status": "healthy", "users_count" : len(users_db)}

#Endpoint Create User
@app.post("/users", response_model = UserOut)
def create_user(user: UserIn):
    #Check if username already exists
    for existing_user in users_db:
        if existing_user["username"] == user.username:
            raise HTTPException(status_code = 400, detail = "Username already exists")
    
    # Create new user with auto-generated ID
    new_user = {
        "id": len(users_db) + 1,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name
    }

    users_db.append(new_user)
    return new_user

#Endpoint get all users
@app.get("/users", response_model = List[UserOut])
def get_users():
    return users_db

#Endoint search user

@app.get("/users/search", response_model=List[UserOut])
def search_users(username: str = None, email: str = None):
    results = []
    for user in users_db:
        if (
            (username is None or user["username"] == username) and
            (email is None or user["email"] == email)
        ):
            results.append(user)
    return results

#Endpoint get specific user
@app.get("/users/{user_id}", response_model = UserOut)
def get_user(user_id: int):
    for user in users_db:
        if user["id"] == user_id:
            return user
    
    raise HTTPException(status_code = 404, detail = "User not found")
            

#Endpoint Update User
@app.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user_updates: UserIn):
    for user in users_db:
        if user["id"] == user_id:
            user["username"] = user_updates.username
            user["email"] = user_updates.email
            user["full_name"] = user_updates.full_name
            return user
    raise HTTPException(status_code=404, detail="User does not exist")


#Endpoint delete user

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    for i, user in enumerate(users_db):
        if user["id"] == user_id:
            deleted_user = users_db.pop(i)
            return {"message": f"User {deleted_user['username']} deleted successfully"}
    
    raise HTTPException(status_code=404, detail="User not found")



    
