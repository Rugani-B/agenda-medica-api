"""
Gera uma chave Fernet para uso em ENCRYPTION_KEY.

Execute uma única vez e guarde a chave em local seguro:
  python scripts/gerar_chave_criptografia.py

Depois configure a variável de ambiente no Railway:
  Settings → Variables → Add Variable
  Nome: ENCRYPTION_KEY
  Valor: (chave gerada acima)

ATENÇÃO: quem perder a chave perde acesso permanente aos dados criptografados.
Faça backup da chave em cofre de senhas (ex.: Bitwarden, 1Password).
"""
from cryptography.fernet import Fernet

chave = Fernet.generate_key().decode()
print("=" * 60)
print("Chave gerada (copie para Railway → ENCRYPTION_KEY):")
print()
print(chave)
print()
print("=" * 60)
print("ATENÇÃO: guarde esta chave em um cofre de senhas agora.")
print("Sem ela, os dados criptografados serão irrecuperáveis.")
