# scripts/popular_especialidades.py
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database.connection import SessionLocal
from app.models.especialidade import Especialidade

db = SessionLocal()

especialidades = [
    "Clínica Geral", "Cardiologia", "Dermatologia",
    "Ginecologia",   "Neurologia",  "Oftalmologia",
    "Ortopedia",     "Pediatria",   "Psiquiatria",
    "Urologia"
]

for nome in especialidades:
    existe = db.query(Especialidade).filter_by(nome=nome).first()
    if not existe:
        db.add(Especialidade(nome=nome))
        print(f"✅ Adicionada: {nome}")
    else:
        print(f"⏭️  Já existe: {nome}")

db.commit()
print("✅ Especialidades cadastradas!")
db.close()
