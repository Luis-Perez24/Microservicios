from services.reservas.app.models import Reserva

_RESERVAS: list[Reserva] = []


def reset() -> None:
    """Limpia el repositorio. Es el punto de partida de todos los provider states."""
    _RESERVAS.clear()


def seed(reserva: Reserva) -> None:
    """Siembra una reserva tal cual (usada por los provider states)."""
    _RESERVAS.append(reserva)


def guardar(usuario_id: str, sala: str, fecha: str, horas: int) -> Reserva:
    """Crea una reserva ACTIVA con id `R-` + (maximo existente, o 1000 si no hay) + 1."""
    numeros = [int(r.id.removeprefix("R-")) for r in _RESERVAS]
    maximo = max(numeros) if numeros else 1000
    reserva = Reserva(
        id=f"R-{maximo + 1}",
        usuario_id=usuario_id,
        sala=sala,
        fecha=fecha,
        horas=horas,
        estado="ACTIVA",
    )
    _RESERVAS.append(reserva)
    return reserva


def listar_por_usuario(usuario_id: str) -> list[Reserva]:
    return [r for r in _RESERVAS if r.usuario_id == usuario_id]


def obtener(reserva_id: str) -> Reserva | None:
    for r in _RESERVAS:
        if r.id == reserva_id:
            return r
    return None