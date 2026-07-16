from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routers import familia, medico

app = FastAPI(title="Agenda Médica")
app.mount("/static", StaticFiles(directory="api/static"), name="static")
app.include_router(familia.router)
app.include_router(medico.router)
