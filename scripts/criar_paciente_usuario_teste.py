"""
Cria um usuário com perfil 'paciente' vinculado a um paciente do banco.

Uso:
  python scripts/criar_paciente_usuario_teste.py [email] [senha] [paciente_id]

Sem argumentos: paciente@teste.com / 123456 / primeiro paciente
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from app.database.connection import SessionLocal
from app.models.usuario import Usuario, PerfilUsuario
from app.models.pacientes import Paciente
from app.models.usuario_paciente import UsuarioPaciente

def main():
    email      = sys.argv[1] if len(sys.argv) > 1 else "paciente@teste.com"
    senha      = sys.argv[2] if len(sys.argv) > 2 else "123456"
    paciente_id = int(sys.argv[3]) if len(sys.argv) > 3 else None

    db = SessionLocal()
    try:
        if paciente_id:
            paciente = db.query(Paciente).filter_by(id=paciente_id).first()
        else:
            paciente = db.query(Paciente).first()

        if not paciente:
            print("Nenhum paciente encontrado.")
            sys.exit(1)

        existente = db.query(Usuario).filter_by(email=email).first()
        if existente:
            existente.perfil     = PerfilUsuario.paciente
            existente.senha_hash = Usuario.gerar_hash(senha)
            existente.ativo      = True
            usuario = existente
            db.flush()
            print(f"Usuário atualizado: {email}")
        else:
            usuario = Usuario(
                nome       = paciente.nome,
                email      = email,
                senha_hash = Usuario.gerar_hash(senha),
                perfil     = PerfilUsuario.paciente,
                ativo      = True,
            )
            db.add(usuario)
            db.flush()
            print(f"Usuário criado: {email} / {senha}")

        # Garante vínculo usuario_paciente
        vinculo = db.query(UsuarioPaciente).filter_by(
            usuario_id=usuario.id, paciente_id=paciente.id
        ).first()
        if not vinculo:
            db.add(UsuarioPaciente(usuario_id=usuario.id, paciente_id=paciente.id))

        db.commit()
        print(f"  → vinculado ao paciente: {paciente.nome} (ID {paciente.id})")
        print(f"  → acesso: /familia/login")
    finally:
        db.close()

if __name__ == "__main__":
    main()
