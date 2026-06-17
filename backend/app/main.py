from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .api.routes import router
from .core.config import get_settings

app = FastAPI(title="OurCore API (Local Mock/No-Supabase)", version="1.0.0", docs_url="/docs")

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Garantir a criação do diretório estático para uploads locais
STATIC_DIR = Path(__file__).resolve().parent / "static" / "uploads"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Montar o diretório estático para servir imagens enviadas localmente
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log de erros para facilitar a depuração local
    print("Erro capturado globalmente:", exc)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": f"Erro interno: {str(exc)}", "code": 500},
    )

app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "ok"}
