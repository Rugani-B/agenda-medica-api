# scripts/popular_especialidades_cfm.py
"""Insere na tabela `especialidades` as 55 especialidades e as 64 áreas de atuação
reconhecidas pelo CFM (Resolução CFM nº 2.472/2026).

Só acrescenta o que falta: não altera nem apaga registros existentes.
Pode ser executado mais de uma vez.
"""
import os
import sys
import unicodedata

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database.connection import SessionLocal
from app.models.especialidade import Especialidade

ESPECIALIDADES = [
    "Acupuntura", "Alergia e Imunologia", "Anestesiologia", "Angiologia", "Cardiologia",
    "Cirurgia Cardiovascular", "Cirurgia da Mão", "Cirurgia de Cabeça e Pescoço",
    "Cirurgia do Aparelho Digestivo", "Cirurgia Geral", "Cirurgia Oncológica",
    "Cirurgia Pediátrica", "Cirurgia Plástica", "Cirurgia Torácica", "Cirurgia Vascular",
    "Clínica Médica", "Coloproctologia", "Dermatologia", "Endocrinologia e Metabologia",
    "Endoscopia", "Gastroenterologia", "Genética Médica", "Geriatria",
    "Ginecologia e Obstetrícia", "Hematologia e Hemoterapia", "Homeopatia", "Infectologia",
    "Mastologia", "Medicina de Emergência", "Medicina de Família e Comunidade",
    "Medicina do Trabalho", "Medicina de Tráfego", "Medicina Esportiva",
    "Medicina Física e Reabilitação", "Medicina Intensiva", "Medicina Legal e Perícia Médica",
    "Medicina Nuclear", "Medicina Preventiva e Social", "Nefrologia", "Neurocirurgia",
    "Neurologia", "Nutrologia", "Oftalmologia", "Oncologia Clínica",
    "Ortopedia e Traumatologia", "Otorrinolaringologia", "Patologia",
    "Patologia Clínica/Medicina Laboratorial", "Pediatria", "Pneumologia", "Psiquiatria",
    "Radiologia e Diagnóstico por Imagem", "Radioterapia", "Reumatologia", "Urologia",
]

# Todas exigem título de especialista prévio
AREAS_DE_ATUACAO = [
    "Administração em Saúde", "Alergia e Imunologia Pediátrica",
    "Angiorradiologia e Cirurgia Endovascular", "Atendimento ao Queimado", "Auditoria Médica",
    "Cardiointensivismo", "Cardiologia Pediátrica", "Cirurgia Bariátrica",
    "Cirurgia Crânio-Maxilo-Facial", "Cirurgia do Trauma", "Cirurgia Videolaparoscópica",
    "Citopatologia", "Densitometria Óssea", "Dor", "Ecocardiografia",
    "Ecografia Vascular com Doppler", "Eletrofisiologia Clínica Invasiva",
    "Emergência Pediátrica", "Endocrinologia Pediátrica", "Endoscopia Digestiva",
    "Endoscopia Ginecológica", "Endoscopia Respiratória", "Ergometria",
    "Estimulação Cardíaca Eletrônica Implantável", "Foniatria", "Gastroenterologia Pediátrica",
    "Hansenologia", "Hematologia e Hemoterapia Pediátrica",
    "Hemodinâmica e Cardiologia Intervencionista", "Hepatologia", "Infectologia Hospitalar",
    "Infectologia Pediátrica", "Mamografia", "Medicina Aeroespacial", "Medicina do Adolescente",
    "Medicina do Sono", "Medicina Fetal", "Medicina Intensiva Pediátrica",
    "Medicina Marítima e Hiperbárica", "Medicina Paliativa", "Medicina Tropical",
    "Nefrologia Pediátrica", "Neonatologia", "Neurofisiologia Clínica", "Neurologia Pediátrica",
    "Neurorradiologia", "Nutrição Parenteral e Enteral",
    "Nutrição Parenteral e Enteral Pediátrica", "Nutrologia Pediátrica", "Oncogenética",
    "Oncologia Pediátrica", "Pneumologia Pediátrica", "Psicogeriatria", "Psicoterapia",
    "Psiquiatria da Infância e Adolescência", "Psiquiatria Forense",
    "Radiologia Intervencionista e Angiorradiologia", "Reprodução Assistida",
    "Reumatologia Pediátrica", "Sexologia", "Toxicologia Médica", "Transplante de Medula Óssea",
    "Ultrassonografia em Ginecologia e Obstetrícia", "Ultrassonografia Geral",
]


def _chave(nome: str) -> str:
    """Compara ignorando acentos e maiúsculas (igual ao índice único do MySQL)."""
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


assert len(ESPECIALIDADES) == 55 and len(AREAS_DE_ATUACAO) == 64

db = SessionLocal()
try:
    existentes = {_chave(e.nome) for e in db.query(Especialidade).all()}
    novas = 0
    for nome in ESPECIALIDADES + AREAS_DE_ATUACAO:
        if _chave(nome) not in existentes:
            db.add(Especialidade(nome=nome))
            existentes.add(_chave(nome))
            novas += 1
    db.commit()
    print(f"Adicionadas: {novas} | ja existiam: {119 - novas} | total na tabela: {db.query(Especialidade).count()}")
finally:
    db.close()
