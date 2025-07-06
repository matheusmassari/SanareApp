from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.users.models import User, UserRole
from app.users.schemas import UserCreate, UserUpdate, UserUpdatePassword
from app.core.security import get_password_hash, verify_password, create_access_token


class UserService:
    """Service for user operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db_session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db_session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.db_session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get list of users with pagination"""
        result = await self.db_session.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_username = await self.get_user_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=user_data.role
        )
        
        self.db_session.add(db_user)
        try:
            await self.db_session.commit()
            await self.db_session.refresh(db_user)
        except IntegrityError:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User creation failed"
            )
        
        return db_user
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Update fields if provided
        if user_data.email is not None:
            # Check if email is already taken by another user
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            user.email = user_data.email
        
        if user_data.username is not None:
            # Check if username is already taken by another user
            existing_user = await self.get_user_by_username(user_data.username)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            user.username = user_data.username
        
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        if user_data.role is not None:
            user.role = user_data.role
        
        try:
            await self.db_session.commit()
            await self.db_session.refresh(user)
        except IntegrityError:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User update failed"
            )
        
        return user
    
    async def update_password(self, user_id: int, password_data: UserUpdatePassword) -> bool:
        """Update user password"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        # Update password
        user.hashed_password = get_password_hash(password_data.new_password)
        
        try:
            await self.db_session.commit()
            return True
        except IntegrityError:
            await self.db_session.rollback()
            return False
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        await self.db_session.delete(user)
        try:
            await self.db_session.commit()
            return True
        except IntegrityError:
            await self.db_session.rollback()
            return False
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def create_access_token_for_user(self, user: User) -> str:
        """Create access token for user"""
        return create_access_token(subject=str(user.id)) 