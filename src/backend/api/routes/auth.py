"""Authentication routes: register, login, logout, me, profile."""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import (
    create_access_token,
    get_jwt_secret_key,
    hash_password,
    verify_password,
)
from backend.api.dependencies import get_current_user, get_db
from backend.models.database import User

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict  # {id, email}


class ProfileUpdateRequest(BaseModel):
    taste_tags_default: str = Field(default="[]")  # JSON array as string
    budget_default: str = Field(default="适中")  # 经济/适中/宽裕


class UserResponse(BaseModel):
    id: str
    email: str
    taste_tags_default: str
    budget_default: str


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create new account. Returns JWT token."""
    from sqlalchemy import select

    # Check if email exists
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=request.email,
        password_hash=hash_password(request.password),
        taste_tags_default="[]",
        budget_default="适中",
    )
    db.add(user)
    await db.commit()

    token = create_access_token(user_id, get_jwt_secret_key())

    return AuthResponse(access_token=token, user={"id": user_id, "email": request.email})


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Log in with email/password. Returns JWT token."""
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id, get_jwt_secret_key())

    return AuthResponse(access_token=token, user={"id": user.id, "email": user.email})


@router.post("/logout")
async def logout():
    """Log out. Client should delete localStorage token."""
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get current user info."""
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        email=user.email,
        taste_tags_default=user.taste_tags_default,
        budget_default=user.budget_default,
    )


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update current user's taste preferences and budget."""
    # Validate taste_tags_default is valid JSON
    try:
        tags = json.loads(request.taste_tags_default)
        if not isinstance(tags, list):
            raise HTTPException(status_code=400, detail="taste_tags_default must be a JSON array")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="taste_tags_default must be valid JSON")

    # Validate budget_default
    valid_budgets = ["经济", "适中", "宽裕"]
    if request.budget_default not in valid_budgets:
        raise HTTPException(status_code=400, detail=f"budget_default must be one of: {valid_budgets}")

    # Update user
    await db.execute(
        update(User)
        .where(User.id == current_user["id"])
        .values(
            taste_tags_default=request.taste_tags_default,
            budget_default=request.budget_default,
        )
    )
    await db.commit()

    # Return updated profile
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one()
    return UserResponse(
        id=user.id,
        email=user.email,
        taste_tags_default=user.taste_tags_default,
        budget_default=user.budget_default,
    )
