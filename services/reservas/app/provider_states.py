from typing import Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.reservas.app import repository
from services.reservas.app.models import Reserva

router = APIRouter()

MENSAJE_ESTADO_DESCONOCIDO = "ESTADO_DESCONOCIDO"

_RESERVA_U100_ACTIVA = Reserva(
    id="R-1001",
    usuario_id="U100",
    sala="SALA-1",
    fecha="2026-09-15",
    horas=2,
    estado="ACTIVA",
)


def _usuario_u100_con_reserva_activa() -> None:
    repository.reset()
    repository.seed(_RESERVA_U100_ACTIVA)


def _repositorio_vacio() -> None:
    repository.reset()


ESTADOS: dict[str, Callable[[], None]] = {
    "el usuario U100 tiene una reserva activa": _usuario_u100_con_reserva_activa,
    "el usuario U200 no tiene reservas": _repositorio_vacio,
    "la reserva R-1001 existe y esta activa": _usuario_u100_con_reserva_activa,
    "la reserva R-9999 no existe": _repositorio_vacio,
    "el sistema acepta nuevas reservas": _repositorio_vacio,
}


class ProviderStateRequest(BaseModel):
    state: str
    params: dict = Field(default_factory=dict)
    action: str = "setup"


@router.post("/_pact/provider-states", response_model=None)
def aplicar_provider_state(solicitud: ProviderStateRequest) -> dict | JSONResponse:
    if solicitud.action != "setup":
        return {}
    handler = ESTADOS.get(solicitud.state)
    if handler is None:
        return JSONResponse(
            status_code=400,
            content={"error": MENSAJE_ESTADO_DESCONOCIDO, "mensaje": solicitud.state},
        )
    handler()
    return {}