# services/administracion/app/main.py
"""API de Administracion: contrato de API, seccion 6.3."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Literal

import httpx
from fastapi import Depends, FastAPI, Path, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StrictBool

from shared.reservas_client import ReservasClient

logger = logging.getLogger(__name__)


class ValidacionReserva(BaseModel):
    reservaId: str = Field(pattern=r"^R-\d+$")
    valida: StrictBool


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


app = FastAPI(title="Servicio de Administracion", lifespan=lifespan)


@app.get(
    "/admin/reservas/{reservaId}/validacion",
    response_model=ValidacionReserva,
    responses={502: {"model": ErrorReservas}},
)
def validar_reserva(
    reserva_id: Annotated[str, Path(alias="reservaId")],
    cliente: Annotated[ReservasClient, Depends(get_reservas_client)],
) -> ValidacionReserva | JSONResponse:
    try:
        resultado = ValidacionReserva.model_validate(
            cliente.verificar_reserva(reserva_id)
        )
        if resultado.reservaId != reserva_id:
            raise ValueError("El proveedor devolvio otra reserva")
        return resultado
    except (httpx.HTTPError, ValueError):
        logger.warning("Fallo al validar reserva", exc_info=True)
        return JSONResponse(
            status_code=502, content=ErrorReservas().model_dump()
        )
