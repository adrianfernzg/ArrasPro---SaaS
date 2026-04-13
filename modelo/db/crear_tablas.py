"""
crear_tablas.py - Script para crear todas las tablas en PostgreSQL.
Ejecutar desde la raíz del proyecto:
    python -m modelo.db.crear_tablas
"""

from modelo.db.db_conexion import engine, Base
# Importamos los modelos para que Base.metadata los registre
from modelo.db.models import Usuario, Contrato, PasswordResetToken


def crear_base_de_datos():
    """Crea todas las tablas definidas en los modelos si no existen."""
    print("🔧 Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente:")
    print("   - usuarios")
    print("   - contratos")
    print("   - password_reset_tokens")


if __name__ == "__main__":
    crear_base_de_datos()
