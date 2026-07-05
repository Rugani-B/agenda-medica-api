from sqlalchemy import or_

from app.database.connection import SessionLocal
from app.models.pacientes import Paciente


class PacienteRepository:

    @staticmethod
    def criar(dados):

        db = SessionLocal()

        try:

            paciente = Paciente(**dados)

            db.add(paciente)

            db.commit()

            return paciente

        finally:
            db.close()

    @staticmethod
    def listar():

        db = SessionLocal()

        try:

            return db.query(Paciente)\
                .order_by(Paciente.nome)\
                .all()

        finally:
            db.close()

    @staticmethod
    def buscar_por_nome(texto):

        db = SessionLocal()

        try:

            return db.query(Paciente)\
                .filter(
                    Paciente.nome.ilike(f"%{texto}%")
                )\
                .order_by(Paciente.nome)\
                .all()

        finally:
            db.close()

    @staticmethod
    def atualizar(paciente_id, dados):

        db = SessionLocal()

        try:

            paciente = db.query(Paciente)\
                .filter(Paciente.id == paciente_id)\
                .first()

            if paciente:

                for campo, valor in dados.items():
                    setattr(paciente, campo, valor)

                db.commit()

            return paciente

        finally:
            db.close()

    @staticmethod
    def excluir(paciente_id):

        db = SessionLocal()

        try:

            paciente = db.query(Paciente)\
                .filter(Paciente.id == paciente_id)\
                .first()

            if paciente:

                db.delete(paciente)

                db.commit()

        finally:
            db.close()