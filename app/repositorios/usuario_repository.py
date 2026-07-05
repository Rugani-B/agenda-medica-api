# app/repositorios/usuario_repository.py
from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.repositorios.base_repository import BaseRepository


class UsuarioRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Usuario, db)

    def buscar_por_email(self, email: str):
        return (
            self.db.query(Usuario)
            .filter(Usuario.email == email)
            .first()
        )

    def buscar_ativos(self):
        return (
            self.db.query(Usuario)
            .filter(Usuario.ativo == True)
            .all()
        )

    def desativar(self, id: int):
        usuario = self.buscar_por_id(id)
        if usuario:
            usuario.ativo = False
            self.db.commit()
            self.db.refresh(usuario)
        return usuario
