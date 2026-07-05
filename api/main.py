from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routers import familia

app = FastAPI(title="Agenda Médica — Familiares")
app.mount("/static", StaticFiles(directory="api/static"), name="static")
app.include_router(familia.router)
