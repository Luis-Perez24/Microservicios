from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from services.reservas.app import repository
from services.reservas.app.models import Reserva, ReservaRequest

router = APIRouter()

MENSAJE_HORAS_INVALIDAS = "La cantidad de horas debe ser mayor a cero"


@router.post("/reservas", response_model=Reserva, status_code=201)
def crear_reserva(solicitud: ReservaRequest) -> Reserva | JSONResponse:
    if solicitud.horas <= 0:
        return JSONResponse(
            status_code=400,
            content={"error": "HORAS_INVALIDAS", "mensaje": MENSAJE_HORAS_INVALIDAS},
        )
    return repository.guardar(
        usuario_id=solicitud.usuario_id,
        sala=solicitud.sala,
        fecha=solicitud.fecha,
        horas=solicitud.horas,
    )


@router.get("/reservas", response_model=list[Reserva])
def reservas_de_usuario(
    usuario_id: str = Query(alias="usuarioId"),
) -> list[Reserva]:
    return repository.listar_por_usuario(usuario_id)


@router.get("/reservas/{reserva_id}/verificacion")
def verificar_reserva(reserva_id: str) -> dict:
    reserva = repository.obtener(reserva_id)
    valida = reserva is not None and reserva.estado == "ACTIVA"
    return {"reservaId": reserva_id, "valida": valida}