"""
OAuth routes for authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.auth import get_current_active_user
from app.users.models import User, OAuthProvider
from app.users.schemas import (
    OAuthLoginRequest, 
    OAuthLoginResponse, 
    OAuthCallbackRequest,
    Token,
    LinkOAuthRequest,
    UnlinkOAuthRequest,
    UserWithOAuth,
    OAuthAccount
)
from app.oauth.service import OAuthService

router = APIRouter()


@router.post("/login", response_model=OAuthLoginResponse)
async def oauth_login(
    request: OAuthLoginRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Initiate OAuth login flow
    """
    oauth_service = OAuthService(session)
    
    authorization_url, state = oauth_service.generate_authorization_url(
        provider=request.provider,
        redirect_uri=request.redirect_uri
    )
    
    return OAuthLoginResponse(
        authorization_url=authorization_url,
        state=state
    )


@router.post("/callback", response_model=Token)
async def oauth_callback(
    provider: OAuthProvider = Query(..., description="OAuth provider"),
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State parameter"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Handle OAuth callback and return access token
    """
    oauth_service = OAuthService(session)
    
    user, access_token = await oauth_service.handle_oauth_callback(
        provider=provider,
        code=code,
        state=state
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/providers")
async def get_available_providers():
    """
    Get list of available OAuth providers
    """
    return {
        "providers": [
            {
                "name": "google",
                "display_name": "Google",
                "icon": "fab fa-google"
            }
            # Add more providers here as they are implemented
        ]
    }


@router.post("/link", response_model=OAuthAccount)
async def link_oauth_account(
    request: LinkOAuthRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Link OAuth account to current user
    """
    oauth_service = OAuthService(session)
    
    oauth_account = await oauth_service.link_oauth_account(
        user_id=current_user.id,
        provider=request.provider,
        code=request.code,
        state=request.state
    )
    
    return oauth_account


@router.delete("/unlink")
async def unlink_oauth_account(
    request: UnlinkOAuthRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Unlink OAuth account from current user
    """
    oauth_service = OAuthService(session)
    
    success = await oauth_service.unlink_oauth_account(
        user_id=current_user.id,
        provider=request.provider
    )
    
    if success:
        return {"message": f"{request.provider.value} account unlinked successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlink OAuth account"
        )


@router.get("/accounts", response_model=list[OAuthAccount])
async def get_oauth_accounts(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get OAuth accounts linked to current user
    """
    oauth_service = OAuthService(session)
    
    oauth_accounts = await oauth_service.get_user_oauth_accounts(current_user.id)
    
    return oauth_accounts


@router.get("/user/complete", response_model=UserWithOAuth)
async def get_current_user_with_oauth(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get current user with OAuth accounts information
    """
    oauth_service = OAuthService(session)
    
    oauth_accounts = await oauth_service.get_user_oauth_accounts(current_user.id)
    
    # Create response with OAuth accounts
    user_data = current_user.__dict__.copy()
    user_data['oauth_accounts'] = oauth_accounts
    
    return UserWithOAuth(**user_data)