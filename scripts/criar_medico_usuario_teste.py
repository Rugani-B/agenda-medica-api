"""
Cria um usuário com perfil 'medico' vinculado ao primeiro médico do banco.

Uso:
  python scripts/criar_medico_usuario_teste.py [email] [senha] [medico_id]

Sem argumentos usa: medico@teste.com / 123456 / primeiro médico cadastrado
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from app.database.connection import SessionLocal
from app.models.usuario import Usuario, PerfilUsuario
from app.models.medico import Medico

def main():
    email     = sys.argv[1] if len(sys.argv) > 1 else "medico@teste.com"
    senha     = sys.argv[2] if len(sys.argv) > 2 else "123456"
    medico_id = int(sys.argv[3]) if len(sys.argv) > 3 else None

    db = SessionLocal()
    try:
        if medico_id:
            medico = db.query(Medico).filter_by(id=medico_id).first()
        else:
            medico = db.query(Medico).first()

        if not medico:
            print("Nenhum médico encontrado no banco. Cadastre um médico primeiro.")
            sys.exit(1)

        existente = db.query(Usuario).filter_by(email=email).first()
        if existente:
            existente.medico_id = medico.id
            existente.perfil    = PerfilUsuario.medico
            existente.senha_hash = Usuario.gerar_hash(senha)
            existente.ativo     = True
            db.commit()
            print(f"Usuário atualizado: {email} → médico: {medico.nome} (ID {medico.id})")
        else:
            u = Usuario(
                nome       = f"Dr(a). {medico.nome}",
                email      = email,
                senha_hash = Usuario.gerar_hash(senha),
                perfil     = PerfilUsuario.medico,
                medico_id  = medico.id,
                ativo      = True,
            )
            db.add(u)
            db.commit()
            print(f"Usuário criado: {email} / {senha}")
            print(f"  → vinculado ao médico: {medico.nome} (ID {medico.id})")
            print(f"  → acesso: /medico/login")
    finally:
        db.close()

if __name__ == "__main__":
    main()
