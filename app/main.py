# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import get_settings
from app.routers import sucursal_inventario, almacen_inventario

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

settings = get_settings()

app = FastAPI(
    title="Inventory Service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajústalo en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers (con prefijo global opcional)
app.include_router(
    sucursal_inventario.router,
)
app.include_router(
    almacen_inventario.router,
)


@app.get("/")
async def root():
    return {
        "message": "Inventory Service API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
