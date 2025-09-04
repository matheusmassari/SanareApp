from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.auth import (
    get_current_active_user, 
    get_current_admin, 
    get_current_manager,
    require_permissions,
    require_role,
    require_role_or_owner
)
from app.core.permissions import Permission, RolePermissions
from app.users.models import User, UserRole
from app.users.schemas import (
    UserCreate, UserPublic, UserUpdate, UserUpdatePassword, 
    UserLogin, Token, UserInDB
)
from app.users.service import UserService
from app.users.dependencies import get_user_service

router = APIRouter()


def serialize_user_public(user: User) -> UserPublic:
    """Serialize SQLAlchemy User into UserPublic schema safely."""
    return UserPublic(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        is_oauth_user=bool(user.is_oauth_user) if user.is_oauth_user is not None else False,
        email_verified=bool(user.email_verified) if user.email_verified is not None else False,
        oauth_providers=user.oauth_providers,
        created_at=user.created_at,
    )


# ========== ROTAS PÚBLICAS (SEM AUTENTICAÇÃO) ==========

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user (public registration - only USER role allowed)
    """
    # Force user role to USER for public registration
    user_data.role = UserRole.USER
    
    user = await user_service.create_user(user_data)
    return serialize_user_public(user)


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


# ========== ROTAS DE PERFIL PRÓPRIO ==========

@router.get("/me", response_model=UserPublic)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile
    """
    return serialize_user_public(current_user)


@router.put("/me", response_model=UserPublic)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user profile (users cannot change their own role)
    """
    # Prevent users from changing their own role
    if user_data.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot change your own role"
        )
    
    updated_user = await user_service.update_user(current_user.id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return serialize_user_public(updated_user)


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


@router.get("/me/hierarchy")
async def get_current_user_hierarchy_info(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get hierarchy information for current user
    """
    hierarchy_info = await user_service.get_user_hierarchy_info(current_user)
    return hierarchy_info


# ========== ROTAS ADMINISTRATIVAS (ADMIN ONLY) ==========

@router.get("/stats/overview")
async def get_user_stats(
    current_user: User = Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user statistics overview - Admin only
    """
    stats = {}
    for role in UserRole:
        count = await user_service.count_users_by_role(role)
        stats[role.value] = count
    
    total_users = sum(stats.values())
    
    return {
        "total_users": total_users,
        "by_role": stats,
        "roles_hierarchy": {
            role.value: {"level": role.level, "count": stats[role.value]} 
            for role in UserRole
        }
    }


@router.get("/roles")
async def get_available_roles(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available roles for current user to assign
    """
    manageable_roles = UserRole.get_accessible_roles(current_user.role)
    
    # Remove roles que não pode gerenciar baseado na hierarquia
    if current_user.role != UserRole.ADMIN:
        manageable_roles = [
            role for role in manageable_roles 
            if role.level < current_user.role.level
        ]
    
    return {
        "available_roles": [
            {
                "value": role.value,
                "level": role.level,
                "can_create": RolePermissions.can_manage_user(current_user.role, role)
            }
            for role in manageable_roles
        ],
        "current_user_role": {
            "value": current_user.role.value,
            "level": current_user.role.level
        }
    }

# ========== ROTAS ESPECÍFICAS POR ROLE ==========

@router.get("/managers", response_model=List[UserPublic])
async def get_managers(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get list of managers - Admin only
    """
    managers = await user_service.get_users_by_role(UserRole.MANAGER, skip=skip, limit=limit)
    return [serialize_user_public(u) for u in managers]


@router.get("/patients", response_model=List[UserPublic])
async def get_patients(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_manager),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get list of patients (USER role) - Manager+ only
    """
    patients = await user_service.get_users_by_role(UserRole.USER, skip=skip, limit=limit)
    return [serialize_user_public(u) for u in patients]

# ========== GESTÃO DE USUÁRIOS (MANAGER+) ==========

@router.get("/", response_model=List[UserPublic])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    role_filter: UserRole = Query(None, description="Filter by role"),
    current_user: User = Depends(require_permissions([Permission.READ_USER])),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get list of users
    - MANAGER: Can see USER level users only
    - ADMIN: Can see all users
    """
    if current_user.role == UserRole.ADMIN:
        # Admin vê todos os usuários
        if role_filter:
            users = await user_service.get_users_by_role(role_filter, skip=skip, limit=limit)
        else:
            users = await user_service.get_users(skip=skip, limit=limit)
    else:
        # Manager só vê usuários que pode gerenciar
        users = await user_service.get_users_manageable_by(current_user, skip=skip, limit=limit)
        
        # Aplicar filtro de role se especificado
        if role_filter:
            users = [u for u in users if u.role == role_filter]
    
    return [serialize_user_public(u) for u in users]


@router.get("/{user_id}", response_model=UserPublic)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_role_or_owner(UserRole.MANAGER)),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user by ID
    - USER: Only own profile
    - MANAGER+: Can see users they can manage + own profile
    """
    # Se não é o próprio usuário, verifica se pode gerenciar
    if current_user.id != user_id:
        can_manage = await user_service.can_user_manage_target(current_user, user_id)
        if not can_manage:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this user"
            )
    
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return serialize_user_public(user)


@router.post("/", response_model=UserPublic)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permissions([Permission.CREATE_USER])),
    user_service: UserService = Depends(get_user_service)
):
    """
    Create new user
    - MANAGER: Can create USER level users only
    - ADMIN: Can create any level users
    """
    # Verificar se pode criar usuário com esse role
    if not await user_service.can_create_user_with_role(current_user, user_data.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You cannot create users with role: {user_data.role.value}"
        )
    
    user = await user_service.create_user(user_data)
    return serialize_user_public(user)


@router.put("/{user_id}", response_model=UserPublic)
async def update_user_by_id(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_permissions([Permission.UPDATE_USER])),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user by ID
    - MANAGER: Can update USER level users only
    - ADMIN: Can update any level users (except role changes need validation)
    """
    # Verificar se pode gerenciar o usuário
    can_manage = await user_service.can_user_manage_target(current_user, user_id)
    if not can_manage:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this user"
        )
    
    # Validar mudança de role se especificada
    if user_data.role is not None:
        is_valid, error_msg = await user_service.validate_role_change(
            current_user, user_id, user_data.role
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )
    
    updated_user = await user_service.update_user(user_id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return serialize_user_public(updated_user)


@router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin),  # Só admin pode deletar
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete user by ID - Admin only
    """
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )
    
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}
