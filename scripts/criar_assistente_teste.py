"""
Cria um usuário assistente de teste e o vincula a pacientes escolhidos.
Execute: python scripts/criar_assistente_teste.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.database.connection import SessionLocal
from app.models.usuario import Usuario, PerfilUsuario
from app.models.pacientes import Paciente
from app.models.usuario_paciente import UsuarioPaciente

db = SessionLocal()

# ── Lista pacientes disponíveis ───────────────────────────────────────────────
pacientes = db.query(Paciente).filter_by(ativo=True).order_by(Paciente.nome).all()
print("\nPacientes ativos no sistema:")
for p in pacientes:
    print(f"  [{p.id}] {p.nome}")

# ── Dados do assistente de teste ──────────────────────────────────────────────
NOME   = "Assistente Teste"
EMAIL  = "assistente@teste.com"
SENHA  = "123456"

# IDs dos pacientes que o assistente poderá ver (ajuste conforme necessário)
# Se deixar vazio [], o assistente não verá nenhum paciente.
PACIENTES_IDS = [p.id for p in pacientes[:2]]   # vincula aos 2 primeiros

# ── Cria ou atualiza usuário ──────────────────────────────────────────────────
usuario = db.query(Usuario).filter_by(email=EMAIL).first()
if usuario:
    print(f"\nUsuário '{EMAIL}' já existe (id={usuario.id}). Atualizando senha e perfil...")
    usuario.senha_hash = Usuario.gerar_hash(SENHA)
    usuario.perfil     = PerfilUsuario.assistente
    usuario.ativo      = True
else:
    usuario = Usuario(
        nome       = NOME,
        email      = EMAIL,
        senha_hash = Usuario.gerar_hash(SENHA),
        perfil     = PerfilUsuario.assistente,
        ativo      = True,
    )
    db.add(usuario)
    db.flush()
    print(f"\nUsuário criado: id={usuario.id}")

db.commit()

# ── Vínculos com pacientes ────────────────────────────────────────────────────
# Remove vínculos antigos deste usuário
db.query(UsuarioPaciente).filter_by(usuario_id=usuario.id).delete()
db.commit()

for pid in PACIENTES_IDS:
    db.add(UsuarioPaciente(usuario_id=usuario.id, paciente_id=pid))
db.commit()

nomes_vinculados = [p.nome for p in pacientes if p.id in PACIENTES_IDS]
print(f"\nAssistente vinculado a {len(PACIENTES_IDS)} paciente(s):")
for n in nomes_vinculados:
    print(f"  - {n}")

print(f"\n--- Login para teste ---")
print(f"  Email : {EMAIL}")
print(f"  Senha : {SENHA}")
print(f"  Perfil: assistente\n")

db.close()
