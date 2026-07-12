import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


def upload_anexo(caminho_local: str, paciente_id: int, nome_arquivo: str) -> str:
    """
    Faz upload do arquivo para o Cloudinary.
    Retorna a URL pública segura (https).
    PDFs são enviados como resource_type='raw'.
    """
    ext = os.path.splitext(nome_arquivo)[1].lower()
    resource_type = "raw" if ext == ".pdf" else "image"

    public_id = f"agenda_medica/paciente_{paciente_id}/{nome_arquivo}"

    result = cloudinary.uploader.upload(
        caminho_local,
        public_id=public_id,
        resource_type=resource_type,
        overwrite=True,
        use_filename=True,
        unique_filename=False,
    )
    return result["secure_url"]


def deletar_anexo(url: str) -> None:
    """Remove o arquivo do Cloudinary a partir da URL."""
    try:
        # Extrai o public_id da URL
        parte = url.split("/upload/")[-1]
        # Remove versão (v12345/) se presente
        if parte.startswith("v") and "/" in parte:
            parte = parte.split("/", 1)[1]
        public_id = parte.rsplit(".", 1)[0]  # remove extensão
        cloudinary.uploader.destroy(public_id, resource_type="raw")
        cloudinary.uploader.destroy(public_id, resource_type="image")
    except Exception:
        pass
