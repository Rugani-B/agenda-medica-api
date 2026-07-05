# app/services/auth_service.py
import bcrypt
from sqlalchemy.orm import Session
from app.models.usuario import Usuario, PerfilUsuario
from app.repositorios.usuario_repository import UsuarioRepository


class AuthService:
    def __init__(self, db: Session):
        self.repo = UsuarioRepository(db)

    def cadastrar_usuario(self, dados: dict) -> Usuario:
        # Verifica email duplicado
        existente = self.repo.buscar_por_email(dados["email"])
        if existente:
            raise ValueError("E-mail já cadastrado.")

        # Gera o hash da senha
        senha_hash = bcrypt.hashpw(
            dados["senha"].encode("utf-8"),
            bcrypt.gensalt()
        )

        usuario = Usuario(
            nome        = dados["nome"],
            email       = dados["email"],
            senha_hash  = senha_hash,
            perfil      = dados["perfil"]
        )
        return self.repo.salvar(usuario)

    def login(self, email: str, senha: str) -> Usuario:
        usuario = self.repo.buscar_por_email(email)

        if not usuario:
            raise ValueError("E-mail ou senha inválidos.")

        if not usuario.ativo:
            raise ValueError("Usuário inativo.")

        senha_correta = bcrypt.checkpw(
            senha.encode("utf-8"),
            usuario.senha_hash
        )
        if not senha_correta:
            raise ValueError("E-mail ou senha inválidos.")

        return usuario

    def alterar_senha(self, id: int, senha_atual: str, nova_senha: str) -> Usuario:
        usuario = self.repo.buscar_por_id(id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")

        senha_correta = bcrypt.checkpw(
            senha_atual.encode("utf-8"),
            usuario.senha_hash
        )
        if not senha_correta:
            raise ValueError("Senha atual incorreta.")

        usuario.senha_hash = bcrypt.hashpw(
            nova_senha.encode("utf-8"),
            bcrypt.gensalt()
        )
        return self.repo.salvar(usuario)

    def desativar_usuario(self, id: int) -> Usuario:
        usuario = self.repo.buscar_por_id(id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")
        return self.repo.desativar(id)
