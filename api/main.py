from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routers import familia, medico, consentimento, assistente

app = FastAPI(title="Agenda Médica")
app.mount("/static", StaticFiles(directory="api/static"), name="static")
app.include_router(familia.router)
app.include_router(medico.router)
app.include_router(consentimento.router)
app.include_router(assistente.router)
