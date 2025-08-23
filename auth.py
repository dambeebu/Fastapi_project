from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from security import verify_password, create_access_token, verify_token
from datetime import timedelta

auth_router = APIRouter()
security = HTTPBearer()

# Import users_db from main (we'll fix this properly later)
# User import users_db

#auth_router = APIRouter

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

@auth_router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest):
    from User import users_db
    #Find user by username
    user = None
    for u in users_db:
        if u["username"] == credentials.username:
            user = u
            break
    
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(user["id"])}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800  # 30 minutes in seconds
    }


# Dependency to get current user from token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    from User import users_db
    for user in users_db:
        if user["id"] == payload["sub"]:  # ✅ match key
            return user
    
    raise HTTPException(status_code=401, detail="User not found")


@auth_router.get("/me")
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user["full_name"]
    }