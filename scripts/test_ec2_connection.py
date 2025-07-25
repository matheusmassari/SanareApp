#!/usr/bin/env python3
"""
Script para testar conexão com PostgreSQL na EC2
"""
import asyncio
import asyncpg
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


async def test_ec2_connection():
    """Test connection to PostgreSQL on EC2"""
    print("🔍 Testando conexão com PostgreSQL na EC2...\n")
    
    # Extract connection details from DATABASE_URL
    database_url = settings.DATABASE_URL
    print(f"📍 URL de conexão: {database_url}")
    
    try:
        # Test basic connection
        print("📡 Tentando conectar...")
        
        conn = await asyncpg.connect(database_url)
        print("✅ Conexão estabelecida com sucesso!")
        
        # Test database access
        print("\n🗄️ Testando acesso ao banco...")
        
        # Get PostgreSQL version
        version = await conn.fetchval("SELECT version()")
        print(f"📊 Versão do PostgreSQL: {version.split(',')[0]}")
        
        # Get database name
        db_name = await conn.fetchval("SELECT current_database()")
        print(f"🏷️ Banco atual: {db_name}")
        
        # Get current user
        current_user = await conn.fetchval("SELECT current_user")
        print(f"👤 Usuário atual: {current_user}")
        
        # Test if we can create tables (check permissions)
        print("\n🔐 Testando permissões...")
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS connection_test (
                    id SERIAL PRIMARY KEY,
                    test_time TIMESTAMP DEFAULT NOW(),
                    message TEXT
                )
            """)
            
            await conn.execute("""
                INSERT INTO connection_test (message) 
                VALUES ('Connection test successful')
            """)
            
            test_count = await conn.fetchval("""
                SELECT COUNT(*) FROM connection_test
            """)
            
            print(f"✅ Permissões OK - {test_count} registros de teste")
            
            # Clean up test table
            await conn.execute("DROP TABLE connection_test")
            print("🧹 Tabela de teste removida")
            
        except Exception as perm_error:
            print(f"⚠️ Aviso de permissões: {perm_error}")
        
        # Test SSL connection info
        print("\n🔒 Informações de SSL:")
        ssl_info = await conn.fetchval("SHOW ssl")
        print(f"📡 SSL ativo: {ssl_info}")
        
        await conn.close()
        print("\n🎉 Teste de conexão concluído com sucesso!")
        
        return True
        
    except asyncpg.exceptions.InvalidAuthorizationSpecificationError:
        print("❌ Erro de autenticação:")
        print("   - Verifique usuário e senha no arquivo .env")
        print("   - Verifique configurações do pg_hba.conf na EC2")
        return False
        
    except asyncpg.exceptions.CannotConnectNowError:
        print("❌ PostgreSQL não está aceitando conexões:")
        print("   - Verifique se o PostgreSQL está rodando na EC2")
        print("   - sudo systemctl status postgresql")
        return False
        
    except OSError as os_error:
        if "Connection refused" in str(os_error):
            print("❌ Conexão recusada:")
            print("   - Verifique o IP da EC2 no arquivo .env")
            print("   - Verifique Security Group da EC2 (porta 5432)")
            print("   - Verifique se sua internet mudou de IP")
        elif "timeout" in str(os_error).lower():
            print("❌ Timeout de conexão:")
            print("   - Verifique firewall da EC2 (ufw status)")
            print("   - Verifique se a EC2 está rodando")
        else:
            print(f"❌ Erro de rede: {os_error}")
        return False
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        print(f"   Tipo: {type(e).__name__}")
        return False


async def detailed_connection_info():
    """Show detailed connection information"""
    print("\n📋 Informações de Configuração:")
    print(f"   Host: {settings.POSTGRES_USER}")
    print(f"   Database: {settings.POSTGRES_DB}")
    print(f"   User: {settings.POSTGRES_USER}")
    print(f"   Debug Mode: {settings.DEBUG}")
    
    # Extract host from DATABASE_URL
    if "://" in settings.DATABASE_URL:
        parts = settings.DATABASE_URL.split("://")[1]
        if "@" in parts:
            host_part = parts.split("@")[1].split("/")[0].split(":")[0]
            print(f"   Host extraído: {host_part}")


def show_troubleshooting_tips():
    """Show troubleshooting tips"""
    print("\n🔧 Dicas de Troubleshooting:")
    print("\n1. Verificar EC2:")
    print("   - Instância está rodando?")
    print("   - Security Group permite porta 5432 do seu IP?")
    print("   - IP público mudou?")
    
    print("\n2. Verificar PostgreSQL na EC2:")
    print("   ssh -i ~/.ssh/your-key.pem ubuntu@EC2_IP")
    print("   sudo systemctl status postgresql")
    print("   sudo ufw status")
    
    print("\n3. Verificar configurações locais:")
    print("   - Arquivo .env existe?")
    print("   - DATABASE_URL está correto?")
    print("   - Dependências instaladas? (pip install -r requirements.txt)")
    
    print("\n4. Testar conexão manual:")
    print("   psql -h EC2_IP -U sanare_user -d sanare_db")


if __name__ == "__main__":
    print("🚀 SanareApp - Teste de Conexão EC2\n")
    
    try:
        # Show configuration info
        asyncio.run(detailed_connection_info())
        
        # Test connection
        success = asyncio.run(test_ec2_connection())
        
        if not success:
            show_troubleshooting_tips()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro ao executar teste: {e}")
        show_troubleshooting_tips()
        sys.exit(1) 