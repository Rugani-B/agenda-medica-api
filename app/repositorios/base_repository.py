# app/repositorios/base_repository.py
from sqlalchemy.orm import Session
from enum import Enum


class BaseRepository:
    def __init__(self, model, db: Session):
        self.model = model
        self.db = db

    def buscar_por_id(self, id: int):
        return self.db.query(self.model).filter(self.model.id == id).first()

    def buscar_todos(self):
        return self.db.query(self.model).all()

    def criar(self, dados: dict):                   # ← novo
        obj = self.model()
        for campo, valor in dados.items():
            if isinstance(valor, Enum):
                valor = valor.value
            setattr(obj, campo, valor)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def salvar(self, obj):
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def deletar(self, id: int):
        obj = self.buscar_por_id(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj

    def atualizar(self, id: int, dados: dict):
        obj = self.buscar_por_id(id)
        if obj:
            for campo, valor in dados.items():
                if isinstance(valor, Enum):
                    valor = valor.value
                setattr(obj, campo, valor)
            self.db.commit()
            self.db.refresh(obj)
        return obj
