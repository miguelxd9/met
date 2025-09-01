#!/usr/bin/env python3
"""
Script para probar la conexión a Azure SQL Server
"""

import pyodbc
import os
from pathlib import Path

def test_connection():
    """
    Probar conexión a Azure SQL Server
    """
    print("🔍 Test de Conexión a Azure SQL Server")
    print("=" * 60)
    print()
    
    # Verificar drivers ODBC
    print("📋 Verificando drivers ODBC...")
    try:
        drivers = pyodbc.drivers()
        sql_server_drivers = [d for d in drivers if 'SQL Server' in d]
        
        if sql_server_drivers:
            print(f"✅ Drivers de SQL Server encontrados: {len(sql_server_drivers)}")
            for driver in sql_server_drivers:
                print(f"   🎯 {driver}")
        else:
            print("❌ No se encontraron drivers de SQL Server")
            return False
    except Exception as e:
        print(f"❌ Error al verificar drivers: {e}")
        return False
    
    print()
    
    # Solicitar credenciales
    print("📝 Ingresa tus credenciales de Azure SQL Server:")
    uid = input("   Usuario (UID): ").strip()
    pwd = input("   Contraseña: ").strip()
    
    if not uid or not pwd:
        print("❌ Usuario y contraseña son requeridos")
        return False
    
    print()
    
    # Construir cadena de conexión
    connection_string = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server=tcp:workint.database.windows.net,1433;"
        f"Database=devops_metrics;"
        f"Uid={uid};"
        f"Pwd={pwd};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    print("🔗 Probando conexión...")
    print(f"   Server: workint.database.windows.net,1433")
    print(f"   Database: devops_metrics")
    print(f"   Usuario: {uid}")
    print()
    
    try:
        # Intentar conexión
        print("🔌 Conectando a Azure SQL Server...")
        conn = pyodbc.connect(connection_string)
        
        print("✅ ¡Conexión exitosa!")
        print()
        
        # Probar query simple
        print("📊 Probando consulta básica...")
        cursor = conn.cursor()
        
        # Obtener versión del servidor
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()
        if version:
            print(f"   Versión SQL Server: {version[0][:100]}...")
        
        # Obtener información de la base de datos
        cursor.execute("SELECT DB_NAME(), USER_NAME()")
        db_info = cursor.fetchone()
        if db_info:
            print(f"   Base de datos conectada: {db_info[0]}")
            print(f"   Usuario conectado: {db_info[1]}")
        
        # Obtener tablas disponibles
        print("\n📋 Tablas disponibles:")
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = cursor.fetchall()
        
        if tables:
            for i, table in enumerate(tables[:10], 1):  # Mostrar solo las primeras 10
                print(f"   {i}. {table[0]}")
            if len(tables) > 10:
                print(f"   ... y {len(tables) - 10} más")
        else:
            print("   No se encontraron tablas")
        
        # Cerrar conexión
        cursor.close()
        conn.close()
        print("\n🔒 Conexión cerrada correctamente")
        
        return True
        
    except pyodbc.Error as e:
        print(f"\n❌ Error de conexión: {e}")
        print(f"   Código de error: {e.args[0] if e.args else 'N/A'}")
        print(f"   Mensaje: {e.args[1] if len(e.args) > 1 else 'N/A'}")
        
        # Sugerencias de solución
        print("\n🔧 Sugerencias de solución:")
        if "Login failed" in str(e):
            print("   • Verifica que el usuario y contraseña sean correctos")
            print("   • Confirma que el usuario tenga permisos en la base de datos")
        elif "Server not found" in str(e):
            print("   • Verifica que el nombre del servidor sea correcto")
            print("   • Confirma que puedas acceder al servidor desde tu red")
        elif "Encryption" in str(e):
            print("   • Verifica que la configuración de encriptación sea correcta")
        
        return False
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return False


def main():
    """Función principal"""
    print("🚀 Test de Conexión a Azure SQL Server")
    print("=" * 60)
    print()
    
    print("📋 Este script te ayudará a probar la conexión a tu base de datos")
    print("   Azure SQL Server y crear la configuración necesaria.")
    print()
    
    # Probar conexión
    success = test_connection()
    
    if success:
        print("\n🎉 ¡Conexión exitosa!")
        print("   Tu base de datos Azure SQL Server está funcionando correctamente")
        
    else:
        print("\n❌ La conexión falló")
        print("   Revisa las sugerencias de solución arriba")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
