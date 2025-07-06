from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.auth import get_current_user, get_current_active_user, get_current_admin_user
from app.users.models import User
from app.users.schemas import (
    UserCreate, UserPublic, UserUpdate, UserUpdatePassword, 
    UserLogin, Token, UserInDB
)
from app.users.service import UserService
from app.users.dependencies import get_user_service

router = APIRouter()


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user
    """
    user = await user_service.create_user(user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    user_service: UserService = Depends(get_user_service)
):
    """
    Login user and return access token
    """
    user = await user_service.authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token = await user_service.create_access_token_for_user(user)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserPublic)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile
    """
    return current_user


@router.put("/me", response_model=UserPublic)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user profile
    """
    updated_user = await user_service.update_user(current_user.id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@router.put("/me/password")
async def update_current_user_password(
    password_data: UserUpdatePassword,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user password
    """
    success = await user_service.update_password(current_user.id, password_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update password"
        )
    return {"message": "Password updated successfully"}


@router.get("/", response_model=List[UserPublic])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get list of users (admin only)
    """
    users = await user_service.get_users(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserPublic)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user by ID (admin only)
    """
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserPublic)
async def update_user_by_id(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user by ID (admin only)
    """
    updated_user = await user_service.update_user(user_id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete user by ID (admin only)
    """
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deleted successfully"} 