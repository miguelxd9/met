#!/usr/bin/env python3
"""
Script para probar la conexión con la API de Bitbucket

Este script verifica que la conexión con Bitbucket funcione correctamente
y muestra información básica del workspace configurado.
"""

import os
import sys
import asyncio

# Agregar el directorio raíz del proyecto al path de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.api.bitbucket_client import BitbucketClient
from src.config.settings import get_settings


async def test_bitbucket_connection():
    """
    Probar la conexión con Bitbucket y mostrar información básica
    """
    print("🔍 Probando conexión con Bitbucket...")
    print("=" * 50)
    
    try:
        # Obtener configuración
        settings = get_settings()
        print(f"🌐 API Base URL: {settings.api_base_url}")
        print(f"👤 Usuario: {settings.bitbucket_username}")
        print(f"⏱️  Timeout: {settings.api_timeout} segundos")
        print(f"🚦 Rate Limit: {settings.api_rate_limit} requests/hora")
        print()
        
        # Crear cliente de Bitbucket
        print("🔌 Creando cliente de Bitbucket...")
        client = BitbucketClient()
        print("✅ Cliente creado exitosamente")
        print()
        
        # Probar conexión básica
        print("📡 Probando conexión básica...")
        
        # Obtener información del workspace
        workspace_slug = "ibkteam"  # Workspace por defecto
        print(f"🏢 Obteniendo información del workspace: {workspace_slug}")
        
        try:
            workspace_info = await client.get_workspace(workspace_slug)
            print(f"✅ Workspace obtenido exitosamente")
            print(f"   📝 Nombre: {workspace_info.get('name', 'N/A')}")
            print(f"   🆔 ID: {workspace_info.get('id', 'N/A')}")
            print(f"   🔒 Privado: {workspace_info.get('is_private', 'N/A')}")
            print(f"   🌐 Website: {workspace_info.get('website', 'N/A')}")
            print(f"   📍 Ubicación: {workspace_info.get('location', 'N/A')}")
            print()
            
            # Mostrar estado del rate limiter
            print("🚦 Estado del Rate Limiter:")
            rate_limiter_status = client.get_rate_limiter_status()
            print(f"   ⏰ Requests restantes: {rate_limiter_status.get('remaining_requests', 'N/A')}")
            print(f"   🔄 Reset time: {rate_limiter_status.get('reset_time', 'N/A')}")
            print()
            
            print("🎉 ¡Conexión con Bitbucket probada exitosamente!")
            print("✅ Todas las funcionalidades básicas están funcionando correctamente")
            
        except Exception as e:
            print(f"❌ Error al obtener información del workspace: {e}")
            print(f"   Tipo de error: {type(e).__name__}")
            return False
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        print(f"   Tipo de error: {type(e).__name__}")
        return False
    
    return True


async def main():
    """Función principal"""
    print("🚀 Test de Conexión con Bitbucket")
    print("=" * 50)
    print()
    
    success = await test_bitbucket_connection()
    
    if success:
        print("\n🎯 Resultado: CONEXIÓN EXITOSA")
        print("   El proyecto está configurado correctamente para trabajar con Bitbucket")
    else:
        print("\n❌ Resultado: CONEXIÓN FALLIDA")
        print("   Revisa la configuración y las credenciales de Bitbucket")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
