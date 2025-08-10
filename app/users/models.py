from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User roles enum"""
    ADMIN = "admin"
    USER = "user"


class OAuthProvider(str, enum.Enum):
    """OAuth providers enum"""
    GOOGLE = "google"
    GITHUB = "github"
    FACEBOOK = "facebook"


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)  # Para foto do perfil
    hashed_password = Column(String, nullable=True)  # Agora nullable para usuários OAuth
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    
    # OAuth fields
    is_oauth_user = Column(Boolean, default=False)  # Indica se é usuário OAuth
    email_verified = Column(Boolean, default=False)  # Verificação de email
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    oauth_accounts = relationship("UserOAuthAccount", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
    
    @property
    def has_password(self) -> bool:
        """Check if user has a password set"""
        return self.hashed_password is not None
    
    @property
    def oauth_providers(self) -> list[str]:
        """Get list of connected OAuth providers"""
        return [account.provider for account in self.oauth_accounts]


class UserOAuthAccount(Base):
    """OAuth account linking table"""
    __tablename__ = "user_oauth_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(Enum(OAuthProvider), nullable=False)
    provider_user_id = Column(String, nullable=False)  # ID do usuário no provider
    provider_user_email = Column(String, nullable=False)  # Email no provider
    provider_user_name = Column(String, nullable=True)  # Nome no provider
    provider_avatar_url = Column(String, nullable=True)  # Avatar no provider
    access_token = Column(Text, nullable=True)  # Token de acesso (criptografado)
    refresh_token = Column(Text, nullable=True)  # Token de refresh (criptografado)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata do provider
    provider_data = Column(Text, nullable=True)  # JSON com dados adicionais
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="oauth_accounts")
    
    def __repr__(self):
        return f"<UserOAuthAccount(user_id={self.user_id}, provider={self.provider}, provider_user_id={self.provider_user_id})>" 