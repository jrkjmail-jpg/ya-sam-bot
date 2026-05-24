from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import analyze, images, instructions
from config.settings import get_settings
from database.session import create_db


settings = get_settings()

app = FastAPI(title="Я сам API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/storage", StaticFiles(directory=settings.storage_dir), name="storage")
app.include_router(analyze.router)
app.include_router(instructions.router)
app.include_router(images.router)


@app.on_event("startup")
def on_startup() -> None:
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    create_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
