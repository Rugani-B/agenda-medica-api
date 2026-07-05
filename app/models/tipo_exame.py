from sqlalchemy import Column, Integer, String, Text
from  app.database.base import Base


class TipoExame(Base):
    __tablename__ = "tipos_exame"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    nome      = Column(String(150), nullable=False, unique=True)
    descricao = Column(Text, nullable=True)

    def __repr__(self):
        return f"<TipoExame {self.nome}>"
