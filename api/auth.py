import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "chave-secreta-padrao")


def gerar_token(responsavel_id: int) -> str:
    raw = f"{responsavel_id}:{SECRET_KEY}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def verificar_token(token: str, responsavel_id: int) -> bool:
    return gerar_token(responsavel_id) == token
