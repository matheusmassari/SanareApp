from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from app.users.models import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    role: UserRole = UserRole.USER


class UserCreate(BaseModel):
    """Schema for creating a user"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    password: str
    role: UserRole = UserRole.USER
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class UserUpdatePassword(BaseModel):
    """Schema for updating user password"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserInDB(UserBase):
    """Schema for user in database"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class UserPublic(BaseModel):
    """Schema for public user information"""
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool
    role: UserRole
    created_at: datetime
    
    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data"""
    user_id: Optional[int] = None 