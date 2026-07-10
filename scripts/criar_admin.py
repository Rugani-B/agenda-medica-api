# scripts/criar_admin.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database.connection import SessionLocal
from app.services.auth_service import AuthService

db = SessionLocal()
service = AuthService(db)

usuario = service.cadastrar_usuario({
    "nome"  : "Administrador",
    "email" : "admin@agenda.com",
    "senha" : "123456",
    "perfil": "admin"
})

print(f"✅ Usuário criado: {usuario.nome} | {usuario.email}")
db.close()
