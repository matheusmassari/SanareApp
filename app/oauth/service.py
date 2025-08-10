"""
OAuth Service for handling OAuth authentication flows
"""
import json
import secrets
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from authlib.integrations.base_client import OAuthError
from authlib.oauth2 import OAuth2Client
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import get_password_hash, create_access_token
from app.users.models import User, UserOAuthAccount, OAuthProvider, UserRole
from app.users.schemas import OAuthUserInfo
from app.users.service import UserService


class OAuthService:
    """Service for OAuth operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.user_service = UserService(db_session)
        self.state_serializer = URLSafeTimedSerializer(
            settings.OAUTH_STATE_SECRET or settings.SECRET_KEY
        )
        
        # OAuth providers configuration
        self.providers_config = {
            OAuthProvider.GOOGLE: {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_url": "https://accounts.google.com/o/oauth2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scopes": ["openid", "email", "profile"],
            }
        }
    
    def _get_provider_config(self, provider: OAuthProvider) -> Dict[str, Any]:
        """Get configuration for OAuth provider"""
        config = self.providers_config.get(provider)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )
        
        if not config["client_id"] or not config["client_secret"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OAuth provider {provider} not configured"
            )
        
        return config
    
    def generate_authorization_url(
        self, 
        provider: OAuthProvider, 
        redirect_uri: str
    ) -> Tuple[str, str]:
        """Generate OAuth authorization URL and state"""
        config = self._get_provider_config(provider)
        
        # Generate secure state
        state_data = {
            "provider": provider.value,
            "redirect_uri": redirect_uri,
            "timestamp": datetime.utcnow().isoformat()
        }
        state = self.state_serializer.dumps(state_data)
        
        # Build authorization URL
        oauth_client = OAuth2Client(
            client_id=config["client_id"],
            redirect_uri=redirect_uri
        )
        
        auth_params = {
            "response_type": "code",
            "client_id": config["client_id"],
            "redirect_uri": redirect_uri,
            "scope": " ".join(config["scopes"]),
            "state": state,
            "access_type": "offline",  # For refresh tokens
            "prompt": "consent"  # Always show consent screen
        }
        
        authorization_url = f"{config['auth_url']}?{urlencode(auth_params)}"
        
        return authorization_url, state
    
    def _verify_state(self, state: str, expected_provider: OAuthProvider) -> Dict[str, Any]:
        """Verify OAuth state parameter"""
        try:
            state_data = self.state_serializer.loads(
                state, 
                max_age=600  # 10 minutes
            )
            
            if state_data.get("provider") != expected_provider.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid OAuth state: provider mismatch"
                )
            
            return state_data
            
        except (BadSignature, SignatureExpired):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OAuth state"
            )
    
    async def _exchange_code_for_token(
        self, 
        provider: OAuthProvider, 
        code: str, 
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        config = self._get_provider_config(provider)
        
        token_data = {
            "grant_type": "authorization_code",
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "redirect_uri": redirect_uri,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config["token_url"],
                data=token_data,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            return response.json()
    
    async def _get_user_info(
        self, 
        provider: OAuthProvider, 
        access_token: str
    ) -> OAuthUserInfo:
        """Get user information from OAuth provider"""
        config = self._get_provider_config(provider)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                config["userinfo_url"],
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info from OAuth provider"
                )
            
            user_data = response.json()
            
            # Normalize user data based on provider
            if provider == OAuthProvider.GOOGLE:
                return OAuthUserInfo(
                    id=user_data["id"],
                    email=user_data["email"],
                    name=user_data.get("name"),
                    picture=user_data.get("picture"),
                    email_verified=user_data.get("verified_email", False)
                )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"User info normalization not implemented for {provider}"
            )
    
    async def _get_oauth_account(
        self, 
        provider: OAuthProvider, 
        provider_user_id: str
    ) -> Optional[UserOAuthAccount]:
        """Get existing OAuth account"""
        result = await self.db_session.execute(
            select(UserOAuthAccount).where(
                UserOAuthAccount.provider == provider,
                UserOAuthAccount.provider_user_id == provider_user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def _create_oauth_account(
        self,
        user_id: int,
        provider: OAuthProvider,
        oauth_user_info: OAuthUserInfo,
        token_data: Dict[str, Any]
    ) -> UserOAuthAccount:
        """Create new OAuth account"""
        oauth_account = UserOAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_user_id=oauth_user_info.id,
            provider_user_email=oauth_user_info.email,
            provider_user_name=oauth_user_info.name,
            provider_avatar_url=oauth_user_info.picture,
            access_token=token_data.get("access_token"),  # Should be encrypted in production
            refresh_token=token_data.get("refresh_token"),  # Should be encrypted in production
            token_expires_at=datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600)),
            provider_data=json.dumps(token_data)
        )
        
        self.db_session.add(oauth_account)
        await self.db_session.commit()
        await self.db_session.refresh(oauth_account)
        
        return oauth_account
    
    async def _update_oauth_account(
        self,
        oauth_account: UserOAuthAccount,
        oauth_user_info: OAuthUserInfo,
        token_data: Dict[str, Any]
    ) -> UserOAuthAccount:
        """Update existing OAuth account"""
        oauth_account.provider_user_email = oauth_user_info.email
        oauth_account.provider_user_name = oauth_user_info.name
        oauth_account.provider_avatar_url = oauth_user_info.picture
        oauth_account.access_token = token_data.get("access_token")
        oauth_account.refresh_token = token_data.get("refresh_token")
        oauth_account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
        oauth_account.provider_data = json.dumps(token_data)
        
        await self.db_session.commit()
        await self.db_session.refresh(oauth_account)
        
        return oauth_account
    
    def _generate_username_from_email(self, email: str) -> str:
        """Generate unique username from email"""
        base_username = email.split("@")[0]
        # Add some randomness to ensure uniqueness
        random_suffix = secrets.token_hex(4)
        return f"{base_username}_{random_suffix}"
    
    async def _create_user_from_oauth(
        self,
        oauth_user_info: OAuthUserInfo,
        provider: OAuthProvider
    ) -> User:
        """Create new user from OAuth information"""
        # Generate unique username
        username = self._generate_username_from_email(oauth_user_info.email)
        
        # Ensure username is unique
        attempts = 0
        while await self.user_service.get_user_by_username(username) and attempts < 10:
            username = self._generate_username_from_email(oauth_user_info.email)
            attempts += 1
        
        if attempts >= 10:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate unique username"
            )
        
        # Create user
        user = User(
            email=oauth_user_info.email,
            username=username,
            full_name=oauth_user_info.name,
            avatar_url=oauth_user_info.picture,
            hashed_password=None,  # OAuth users don't have passwords initially
            is_oauth_user=True,
            email_verified=oauth_user_info.email_verified,
            role=UserRole.USER
        )
        
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        
        return user
    
    async def handle_oauth_callback(
        self,
        provider: OAuthProvider,
        code: str,
        state: str
    ) -> Tuple[User, str]:
        """Handle OAuth callback and return user with access token"""
        # Verify state
        state_data = self._verify_state(state, provider)
        redirect_uri = state_data["redirect_uri"]
        
        # Exchange code for token
        token_data = await self._exchange_code_for_token(
            provider, code, redirect_uri
        )
        
        # Get user info from provider
        oauth_user_info = await self._get_user_info(
            provider, token_data["access_token"]
        )
        
        # Check if OAuth account already exists
        oauth_account = await self._get_oauth_account(
            provider, oauth_user_info.id
        )
        
        if oauth_account:
            # Update existing OAuth account
            oauth_account = await self._update_oauth_account(
                oauth_account, oauth_user_info, token_data
            )
            
            # Get user
            user = await self.user_service.get_user_by_id(oauth_account.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="OAuth account exists but user not found"
                )
        else:
            # Check if user exists with this email
            user = await self.user_service.get_user_by_email(oauth_user_info.email)
            
            if user:
                # Link OAuth account to existing user
                oauth_account = await self._create_oauth_account(
                    user.id, provider, oauth_user_info, token_data
                )
                
                # Update user info if needed
                if not user.avatar_url and oauth_user_info.picture:
                    user.avatar_url = oauth_user_info.picture
                if not user.email_verified and oauth_user_info.email_verified:
                    user.email_verified = oauth_user_info.email_verified
                
                await self.db_session.commit()
            else:
                # Create new user
                user = await self._create_user_from_oauth(oauth_user_info, provider)
                
                # Create OAuth account
                oauth_account = await self._create_oauth_account(
                    user.id, provider, oauth_user_info, token_data
                )
        
        # Create access token for our system
        access_token = await self.user_service.create_access_token_for_user(user)
        
        return user, access_token
    
    async def link_oauth_account(
        self,
        user_id: int,
        provider: OAuthProvider,
        code: str,
        state: str
    ) -> UserOAuthAccount:
        """Link OAuth account to existing user"""
        # Verify state
        state_data = self._verify_state(state, provider)
        redirect_uri = state_data["redirect_uri"]
        
        # Get user
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Exchange code for token
        token_data = await self._exchange_code_for_token(
            provider, code, redirect_uri
        )
        
        # Get user info from provider
        oauth_user_info = await self._get_user_info(
            provider, token_data["access_token"]
        )
        
        # Check if OAuth account already exists
        existing_oauth_account = await self._get_oauth_account(
            provider, oauth_user_info.id
        )
        
        if existing_oauth_account:
            if existing_oauth_account.user_id == user_id:
                # Update existing account
                return await self._update_oauth_account(
                    existing_oauth_account, oauth_user_info, token_data
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"This {provider.value} account is already linked to another user"
                )
        
        # Create new OAuth account
        return await self._create_oauth_account(
            user_id, provider, oauth_user_info, token_data
        )
    
    async def unlink_oauth_account(
        self,
        user_id: int,
        provider: OAuthProvider
    ) -> bool:
        """Unlink OAuth account from user"""
        # Get user
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user has password - can't unlink if it's the only auth method
        if not user.has_password:
            # Count OAuth accounts
            result = await self.db_session.execute(
                select(UserOAuthAccount).where(UserOAuthAccount.user_id == user_id)
            )
            oauth_accounts = result.scalars().all()
            
            if len(oauth_accounts) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot unlink the only authentication method. Set a password first."
                )
        
        # Find and delete OAuth account
        result = await self.db_session.execute(
            select(UserOAuthAccount).where(
                UserOAuthAccount.user_id == user_id,
                UserOAuthAccount.provider == provider
            )
        )
        oauth_account = result.scalar_one_or_none()
        
        if not oauth_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {provider.value} account linked to this user"
            )
        
        await self.db_session.delete(oauth_account)
        await self.db_session.commit()
        
        return True
    
    async def get_user_oauth_accounts(self, user_id: int) -> list[UserOAuthAccount]:
        """Get all OAuth accounts for a user"""
        result = await self.db_session.execute(
            select(UserOAuthAccount).where(UserOAuthAccount.user_id == user_id)
        )
        return result.scalars().all()