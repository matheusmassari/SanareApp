from enum import Enum
from typing import List
from app.users.models import UserRole


class Permission(str, Enum):
    """Application permissions"""
    # User management
    CREATE_USER = "CREATE_USER"
    READ_USER = "READ_USER"  
    UPDATE_USER = "UPDATE_USER"
    DELETE_USER = "DELETE_USER"
    
    # Profile management
    READ_OWN_PROFILE = "READ_OWN_PROFILE"
    UPDATE_OWN_PROFILE = "UPDATE_OWN_PROFILE"
    
    # Medical records (exemplos para futuras features)
    READ_MEDICAL_RECORDS = "READ_MEDICAL_RECORDS"
    CREATE_MEDICAL_RECORDS = "CREATE_MEDICAL_RECORDS"
    UPDATE_MEDICAL_RECORDS = "UPDATE_MEDICAL_RECORDS"
    
    # System administration
    MANAGE_SYSTEM = "MANAGE_SYSTEM"
    VIEW_ANALYTICS = "VIEW_ANALYTICS"


class RolePermissions:
    """Define permissions for each role"""
    
    PERMISSIONS_MAP = {
        UserRole.USER: [
            Permission.READ_OWN_PROFILE,
            Permission.UPDATE_OWN_PROFILE,
        ],
        
        UserRole.MANAGER: [
            # Herda permissões de USER
            Permission.READ_OWN_PROFILE,
            Permission.UPDATE_OWN_PROFILE,
            # Permissões específicas de médico/especialista
            Permission.READ_USER,
            Permission.CREATE_USER,  # Pode criar pacientes
            Permission.READ_MEDICAL_RECORDS,
            Permission.CREATE_MEDICAL_RECORDS,
            Permission.UPDATE_MEDICAL_RECORDS,
            Permission.VIEW_ANALYTICS,
        ],
        
        UserRole.ADMIN: [
            # Herda todas as permissões anteriores + administrativas
            Permission.READ_OWN_PROFILE,
            Permission.UPDATE_OWN_PROFILE,
            Permission.CREATE_USER,
            Permission.READ_USER,
            Permission.UPDATE_USER,
            Permission.DELETE_USER,
            Permission.READ_MEDICAL_RECORDS,
            Permission.CREATE_MEDICAL_RECORDS,
            Permission.UPDATE_MEDICAL_RECORDS,
            Permission.MANAGE_SYSTEM,
            Permission.VIEW_ANALYTICS,
        ]
    }
    
    @classmethod
    def get_permissions(cls, role: UserRole) -> List[Permission]:
        """Get all permissions for a role"""
        return cls.PERMISSIONS_MAP.get(role, [])
    
    @classmethod
    def has_permission(cls, role: UserRole, permission: Permission) -> bool:
        """Check if role has specific permission"""
        return permission in cls.get_permissions(role)
    
    @classmethod
    def can_manage_user(cls, manager_role: UserRole, target_role: UserRole) -> bool:
        """Check if manager can manage target user"""
        # Admin pode gerenciar todos
        if manager_role == UserRole.ADMIN:
            return True
        
        # Manager pode gerenciar apenas usuários de nível inferior
        if manager_role == UserRole.MANAGER:
            return target_role == UserRole.USER
        
        # User não pode gerenciar outros usuários
        return False
