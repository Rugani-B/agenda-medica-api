"""
Criptografia simétrica (Fernet / AES-128-CBC + HMAC-SHA256) para campos sensíveis.

Configure a variável de ambiente ENCRYPTION_KEY com uma chave Fernet de 32 bytes em
base64-urlsafe. Para gerar uma chave:

    python scripts/gerar_chave_criptografia.py

Sem a chave os dados são gravados em texto claro (compatibilidade com ambiente de dev
sem variável configurada); o prefixo "enc1:" permite identificar registros já
criptografados e diferenciar de dados legados.
"""
import hashlib
import json
import os

from cryptography.fernet import Fernet, InvalidToken

_KEY: bytes | None = None


def _fernet() -> Fernet | None:
    global _KEY
    raw = os.getenv("ENCRYPTION_KEY", "")
    if not raw:
        return None
    if _KEY != raw.encode():
        _KEY = raw.encode()
    try:
        return Fernet(_KEY)
    except Exception:
        return None


_PREFIX = "enc1:"


def encrypt(value: str | None) -> str | None:
    if value is None:
        return None
    f = _fernet()
    if f is None:
        return value  # sem chave → grava em claro
    return _PREFIX + f.encrypt(value.encode("utf-8")).decode()


def decrypt(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.startswith(_PREFIX):
        return value  # dado legado ou não criptografado
    f = _fernet()
    if f is None:
        return value
    try:
        return f.decrypt(value[len(_PREFIX):].encode()).decode("utf-8")
    except InvalidToken:
        return value  # retorna bruto se chave errada (não apaga dado)


def encrypt_json(obj) -> str | None:
    if obj is None:
        return None
    return encrypt(json.dumps(obj, ensure_ascii=False))


def decrypt_json(value: str | None) -> dict | list | None:
    if value is None:
        return None
    raw = decrypt(value)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return {}


def cpf_hash(cpf: str) -> str:
    """SHA-256 dos dígitos do CPF — usado para lookup sem expor o valor."""
    digits = "".join(c for c in cpf if c.isdigit())
    return hashlib.sha256(digits.encode()).hexdigest()
