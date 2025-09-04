from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import datetime
from app.users.models import UserRole, OAuthProvider


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
    
    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @field_validator('username')
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
    
    @field_validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserInDB(UserBase):
    """Schema for user in database"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    """Schema for public user information"""
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    role: str
    is_oauth_user: bool = False
    email_verified: bool = False
    oauth_providers: List[str] = Field(default_factory=list)
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


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


# OAuth Schemas
class OAuthUserInfo(BaseModel):
    """Schema for OAuth user information from provider"""
    id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    email_verified: bool = False


class OAuthLoginRequest(BaseModel):
    """Schema for OAuth login request"""
    provider: OAuthProvider
    redirect_uri: str


class OAuthLoginResponse(BaseModel):
    """Schema for OAuth login response"""
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """Schema for OAuth callback"""
    code: str
    state: str
    provider: OAuthProvider


class OAuthAccount(BaseModel):
    """Schema for OAuth account information"""
    id: int
    provider: OAuthProvider
    provider_user_id: str
    provider_user_email: str
    provider_user_name: Optional[str] = None
    provider_avatar_url: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserWithOAuth(UserPublic):
    """Schema for user with OAuth accounts"""
    oauth_accounts: List[OAuthAccount] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class LinkOAuthRequest(BaseModel):
    """Schema for linking OAuth account to existing user"""
    provider: OAuthProvider
    code: str
    state: str


class UnlinkOAuthRequest(BaseModel):
    """Schema for unlinking OAuth account"""
    provider: OAuthProvider 