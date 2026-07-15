import os
import httpx

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pfldafgmzawhuzqxdtuy.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
BUCKET = "anexos"


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }


def upload_pdf(caminho_local: str, paciente_id: int, nome_arquivo: str) -> str:
    path = f"paciente_{paciente_id}/{nome_arquivo}"
    with open(caminho_local, "rb") as f:
        data = f.read()

    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{path}"
    r = httpx.put(
        url,
        content=data,
        headers={**_headers(), "Content-Type": "application/pdf"},
        timeout=60,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Supabase upload falhou: {r.status_code} {r.text}")

    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{path}"


def deletar_pdf(url: str) -> None:
    try:
        path = url.split(f"/object/public/{BUCKET}/")[-1]
        r = httpx.delete(
            f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{path}",
            headers=_headers(),
            timeout=15,
        )
    except Exception:
        pass
