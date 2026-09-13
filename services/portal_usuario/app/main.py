# services/portal_usuario/app/main.py
"""API del Portal de Usuario: contrato de API, seccion 6.3."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated, Literal

import httpx
from fastapi import Depends, FastAPI, Path, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from shared.reservas_client import ReservasClient

logger = logging.getLogger(__name__)


class Reserva(BaseModel):
    id: str = Field(pattern=r"^R-\d+$")
    usuarioId: str = Field(pattern=r"^U\d+$")
    sala: str = Field(pattern=r"^SALA-\d+$")
    fecha: date
    horas: int = Field(gt=0, strict=True)
    estado: Literal["ACTIVA", "CANCELADA"]


class ReservasUsuario(BaseModel):
    usuarioId: str
    reservas: list[Reserva]


class ErrorReservas(BaseModel):
    error: Literal["RESERVAS_NO_DISPONIBLE"] = "RESERVAS_NO_DISPONIBLE"
    mensaje: str = "No se pudo consultar el Servicio de Reservas"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    cliente = ReservasClient(os.getenv("RESERVAS_URL", "http://localhost:8001"))
    app.state.reservas_client = cliente
    try:
        yield
    finally:
        # El cliente compartido actual no expone close(); liberar su pool aqui.
        cliente._client.close()


def get_reservas_client(request: Request) -> ReservasClient:
    """Dependencia reemplazable mediante app.dependency_overrides."""
    return request.app.state.reservas_client


app = FastAPI(title="Portal de Usuario", lifespan=lifespan)


@app.get(
    "/portal/usuarios/{usuarioId}/reservas",
    response_model=ReservasUsuario,
    responses={502: {"model": ErrorReservas}},
)
def consultar_reservas(
    usuario_id: Annotated[str, Path(alias="usuarioId")],
    cliente: Annotated[ReservasClient, Depends(get_reservas_client)],
) -> ReservasUsuario | JSONResponse:
    # La ruta sincrona ejecuta el cliente httpx sin bloquear el event loop.
    try:
        resultado = ReservasUsuario(
            usuarioId=usuario_id,
            reservas=cliente.reservas_de_usuario(usuario_id),
        )
        if any(reserva.usuarioId != usuario_id for reserva in resultado.reservas):
            raise ValueError("El proveedor devolvio reservas de otro usuario")
        return resultado
    except (httpx.HTTPError, ValueError):
        logger.warning("Fallo al consultar reservas", exc_info=True)
        return JSONResponse(
            status_code=502, content=ErrorReservas().model_dump()
        )
