"""
Migração: adiciona criptografia em repouso nos campos sensíveis de consentimentos.

Alterações no schema:
  - consentimentos.titular_cpf_hash  VARCHAR(64)  (novo — SHA-256 do CPF)
  - consentimentos.titular_snapshot  LONGTEXT     (era JSON → agora criptografado)
  - consentimentos.representante_legal TEXT       (era JSON → agora criptografado)
  - consentimentos.assinatura_png_b64 LONGTEXT    (era TEXT → agora criptografado)

Execute com ENCRYPTION_KEY já configurado no ambiente:
  python scripts/migrar_criptografia.py

Execute uma única vez em produção. Seguro re-executar: detecta e pula registros
já migrados pelo prefixo "enc1:".
"""
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.database.connection import SessionLocal
from app.services.crypto_service import encrypt_json, encrypt, cpf_hash


def migrar():
    db = SessionLocal()
    conn = db.connection()

    # ── 1. Adicionar coluna titular_cpf_hash ─────────────────────────────────
    print("Verificando coluna titular_cpf_hash...")
    r = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'consentimentos' "
        "AND COLUMN_NAME = 'titular_cpf_hash'"
    ))
    if r.fetchone()[0]:
        print("  → já existe.")
    else:
        conn.execute(text(
            "ALTER TABLE consentimentos "
            "ADD COLUMN titular_cpf_hash VARCHAR(64) NULL AFTER titular_id, "
            "ADD INDEX idx_cons_cpf_hash (titular_cpf_hash)"
        ))
        print("  → coluna adicionada.")

    # ── 2. Converter titular_snapshot de JSON para LONGTEXT ───────────────────
    print("Verificando tipo da coluna titular_snapshot...")
    r = conn.execute(text(
        "SELECT DATA_TYPE FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'consentimentos' "
        "AND COLUMN_NAME = 'titular_snapshot'"
    ))
    tipo = (r.fetchone() or [""])[0].lower()
    if "json" in tipo:
        conn.execute(text(
            "ALTER TABLE consentimentos "
            "MODIFY COLUMN titular_snapshot LONGTEXT NOT NULL"
        ))
        print("  → convertida para LONGTEXT.")
    else:
        print(f"  → já é {tipo}, sem alteração.")

    # ── 3. Converter representante_legal de JSON para TEXT ────────────────────
    print("Verificando tipo da coluna representante_legal...")
    r = conn.execute(text(
        "SELECT DATA_TYPE FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'consentimentos' "
        "AND COLUMN_NAME = 'representante_legal'"
    ))
    tipo = (r.fetchone() or [""])[0].lower()
    if "json" in tipo:
        conn.execute(text(
            "ALTER TABLE consentimentos "
            "MODIFY COLUMN representante_legal TEXT NULL"
        ))
        print("  → convertida para TEXT.")
    else:
        print(f"  → já é {tipo}, sem alteração.")

    db.commit()

    # ── 4. Criptografar registros existentes ──────────────────────────────────
    print("\nCriptografando registros existentes...")
    rows = conn.execute(text(
        "SELECT id, titular_snapshot, representante_legal, assinatura_png_b64, "
        "titular_cpf_hash FROM consentimentos"
    )).fetchall()

    atualizados = 0
    for row in rows:
        rid, snap_raw, rep_raw, assin_raw, cpf_h = row

        # Detecta se já foi criptografado
        ja_enc = isinstance(snap_raw, str) and snap_raw.startswith("enc1:")

        # Parseia snapshot (pode ser dict do MySQL JSON ou string)
        if isinstance(snap_raw, dict):
            snap_dict = snap_raw
        elif isinstance(snap_raw, str):
            try:
                snap_dict = json.loads(snap_raw) if not ja_enc else None
            except Exception:
                snap_dict = None
        else:
            snap_dict = None

        # Parseia representante_legal
        if isinstance(rep_raw, dict):
            rep_dict = rep_raw
        elif isinstance(rep_raw, str):
            try:
                rep_dict = json.loads(rep_raw) if rep_raw and not rep_raw.startswith("enc1:") else None
            except Exception:
                rep_dict = None
        else:
            rep_dict = None

        # CPF hash
        novo_hash = cpf_h
        if snap_dict and not novo_hash:
            cpf_val = snap_dict.get("cpf", "")
            if cpf_val:
                novo_hash = cpf_hash(cpf_val)

        # Criptografa somente o que ainda não foi
        novo_snap = encrypt_json(snap_dict) if snap_dict else snap_raw
        novo_rep  = encrypt_json(rep_dict)  if rep_dict  else rep_raw

        assin_enc = assin_raw
        if assin_raw and not assin_raw.startswith("enc1:"):
            assin_enc = encrypt(assin_raw)

        conn.execute(text(
            "UPDATE consentimentos "
            "SET titular_snapshot = :snap, representante_legal = :rep, "
            "    assinatura_png_b64 = :assin, titular_cpf_hash = :h "
            "WHERE id = :id"
        ), {
            "snap":  novo_snap,
            "rep":   novo_rep,
            "assin": assin_enc,
            "h":     novo_hash,
            "id":    rid,
        })
        atualizados += 1

    db.commit()
    print(f"  → {atualizados} registro(s) processado(s).")
    print("\nMigração concluída com sucesso.")
    db.close()


if __name__ == "__main__":
    if not os.getenv("ENCRYPTION_KEY"):
        print("ERRO: variável ENCRYPTION_KEY não configurada.")
        print("Configure-a antes de executar a migração.")
        sys.exit(1)
    try:
        migrar()
    except Exception as e:
        print(f"Erro: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
