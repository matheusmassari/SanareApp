from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import verify_token
from app.users.models import User, UserRole
from app.users.service import UserService
from app.core.permissions import Permission, RolePermissions

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    # Verify token
    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    user_service = UserService(session)
    user = await user_service.get_user_by_id(int(user_id))
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (not disabled)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user with admin privileges
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user 

def require_permissions(required_permissions: List[Permission]):
    """Dependency factory for permission-based access control"""
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_permissions = RolePermissions.get_permissions(current_user.role)
        
        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission.value}"
                )
        
        return current_user
    
    return permission_checker


def require_role(required_role: UserRole):
    """Dependency factory for role-based access control"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.role.can_access(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role level. Required: {required_role.value} or higher"
            )
        
        return current_user
    
    return role_checker


def require_role_or_owner(required_role: UserRole):
    """Allow access if user has required role OR is the resource owner"""
    def role_or_owner_checker(
        target_user_id: int,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Se é o próprio usuário, permite acesso
        if current_user.id == target_user_id:
            return current_user
        
        # Senão, verifica se tem o role necessário
        if not current_user.role.can_access(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only access your own resources or need higher privileges."
            )
        
        return current_user
    
    return role_or_owner_checker


# Dependências específicas por nível
get_current_manager = require_role(UserRole.MANAGER)
get_current_admin = require_role(UserRole.ADMIN)

# Dependências específicas por permissão
require_user_management = require_permissions([Permission.CREATE_USER, Permission.UPDATE_USER])
require_user_read = require_permissions([Permission.READ_USER])