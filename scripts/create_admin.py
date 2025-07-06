#!/usr/bin/env python3
"""
Script para criar usuário administrador inicial
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import async_session_factory
from app.users.models import User, UserRole
from app.users.schemas import UserCreate
from app.users.service import UserService


async def create_admin_user():
    """Create initial admin user"""
    async with async_session_factory() as session:
        user_service = UserService(session)
        
        # Check if admin already exists
        admin_user = await user_service.get_user_by_email("admin@sanareapp.com")
        if admin_user:
            print("❌ Admin user already exists!")
            return
        
        # Create admin user
        admin_data = UserCreate(
            email="admin@sanareapp.com",
            username="admin",
            full_name="Administrator",
            password="admin123456",  # Change this in production!
            role=UserRole.ADMIN
        )
        
        try:
            admin_user = await user_service.create_user(admin_data)
            print(f"✅ Admin user created successfully!")
            print(f"   Email: {admin_user.email}")
            print(f"   Username: {admin_user.username}")
            print(f"   Role: {admin_user.role}")
            print(f"   🚨 Remember to change the default password!")
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")


if __name__ == "__main__":
    asyncio.run(create_admin_user()) 