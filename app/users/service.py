from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from fastapi import HTTPException, status

from app.users.models import User, UserRole
from app.users.schemas import UserCreate, UserUpdate, UserUpdatePassword
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.permissions import RolePermissions


class UserService:
    """Service for user operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db_session.execute(
            select(User)
            .options(selectinload(User.oauth_accounts))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db_session.execute(
            select(User)
            .options(selectinload(User.oauth_accounts))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.db_session.execute(
            select(User)
            .options(selectinload(User.oauth_accounts))
            .where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get list of users with pagination"""
        result = await self.db_session.execute(
            select(User)
            .options(selectinload(User.oauth_accounts))
            .offset(skip).limit(limit)
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
    
    # ========== MÉTODOS PARA HIERARQUIA ==========
    
    async def can_user_manage_target(
        self, 
        manager_user: User, 
        target_user_id: int
    ) -> bool:
        """Check if manager can manage target user"""
        target_user = await self.get_user_by_id(target_user_id)
        if not target_user:
            return False
        
        return RolePermissions.can_manage_user(manager_user.role, target_user.role)
    
    async def get_users_manageable_by(
        self, 
        manager_user: User, 
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users that can be managed by the given user"""
        manageable_roles = UserRole.get_accessible_roles(manager_user.role)
        
        # Remove o próprio role do manager da lista se não for admin
        # Admin pode gerenciar outros admins, mas manager não gerencia outros managers
        if manager_user.role != UserRole.ADMIN:
            manageable_roles = [
                role for role in manageable_roles 
                if role.level < manager_user.role.level
            ]
        
        if not manageable_roles:
            return []
        
        result = await self.db_session.execute(
            select(User)
            .options(selectinload(User.oauth_accounts))
            .where(User.role.in_(manageable_roles))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_users_by_role(
        self, 
        role: UserRole, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """Get users by specific role"""
        result = await self.db_session.execute(
            select(User)
            .options(selectinload(User.oauth_accounts))
            .where(User.role == role)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_users_by_roles(
        self, 
        roles: List[UserRole], 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """Get users by multiple roles"""
        if not roles:
            return []
        
        result = await self.db_session.execute(
            select(User)
            .options(selectinload(User.oauth_accounts))
            .where(User.role.in_(roles))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def count_users_by_role(self, role: UserRole) -> int:
        """Count users by role"""
        result = await self.db_session.execute(
            select(func.count(User.id)).where(User.role == role)
        )
        return result.scalar() or 0
    
    async def can_create_user_with_role(
        self, 
        creator_user: User, 
        target_role: UserRole
    ) -> bool:
        """Check if creator can create user with target role"""
        return RolePermissions.can_manage_user(creator_user.role, target_role)
    
    async def validate_role_change(
        self, 
        changer_user: User, 
        target_user_id: int, 
        new_role: UserRole
    ) -> tuple[bool, str]:
        """
        Validate if user can change another user's role
        Returns (is_valid, error_message)
        """
        target_user = await self.get_user_by_id(target_user_id)
        if not target_user:
            return False, "Target user not found"
        
        # Não pode alterar o próprio role (evita escalação de privilégios)
        if changer_user.id == target_user_id:
            return False, "You cannot change your own role"
        
        # Verificar se pode gerenciar o usuário atual
        if not RolePermissions.can_manage_user(changer_user.role, target_user.role):
            return False, f"You cannot manage users with role: {target_user.role.value}"
        
        # Verificar se pode criar usuário com o novo role
        if not RolePermissions.can_manage_user(changer_user.role, new_role):
            return False, f"You cannot assign role: {new_role.value}"
        
        return True, ""
    
    async def get_user_hierarchy_info(self, user: User) -> dict:
        """Get hierarchy information for a user"""
        manageable_roles = UserRole.get_accessible_roles(user.role)
        
        # Contar usuários por role que pode gerenciar
        role_counts = {}
        for role in manageable_roles:
            if user.role != UserRole.ADMIN and role.level >= user.role.level:
                continue  # Manager não conta outros managers/admins
            count = await self.count_users_by_role(role)
            role_counts[role.value] = count
        
        return {
            "user_role": user.role.value,
            "role_level": user.role.level,
            "manageable_roles": [role.value for role in manageable_roles],
            "role_counts": role_counts,
            "total_manageable_users": sum(role_counts.values())
        }
