from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.security import DEMO_USERS, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    email: str
    employee_id: str | None = None

@router.post("/token", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = DEMO_USERS.get(payload.email.lower())
    if not user or user["password"] != payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. In demo mode, refer to demo users in the login card.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_access_token({
        "sub": user["email"],
        "role": user["role"],
        "name": user["name"],
        "employee_id": user.get("employee_id"),
    })
    
    return TokenResponse(
        access_token=token,
        role=user["role"],
        name=user["name"],
        email=user["email"],
        employee_id=user.get("employee_id"),
    )

