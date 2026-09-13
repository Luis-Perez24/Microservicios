from collections.abc import Generator
from pathlib import Path

import pytest
from pact import Pact, match

from shared.reservas_client import HorasInvalidasError, ReservasClient

PACTS_DIR = Path(__file__).resolve().parents[3] / "pacts"


@pytest.fixture(scope="module")
def pact() -> Generator[Pact, None, None]:
    pact = Pact("AplicacionReserva", "ServicioReservas").with_specification("V4")

    (
        pact.upon_receiving("una solicitud de reserva valida")
        .given("el sistema acepta nuevas reservas")
        .with_request("POST", "/reservas")
        .with_body(
            {
                "usuarioId": "U100",
                "sala": "SALA-1",
                "fecha": "2026-09-15",
                "horas": 2,
            },
            content_type="application/json",
        )
        .will_respond_with(201)
        .with_body(
            {
                "id": match.regex("R-1001", regex=r"^R-\d+$"),
                "usuarioId": "U100",
                "sala": "SALA-1",
                "fecha": "2026-09-15",
                "horas": 2,
                "estado": "ACTIVA",
            },
            content_type="application/json",
        )
    )
    (
        pact.upon_receiving("una solicitud de reserva con horas invalidas")
        .given("el sistema acepta nuevas reservas")
        .with_request("POST", "/reservas")
        .with_body(
            {
                "usuarioId": "U100",
                "sala": "SALA-1",
                "fecha": "2026-09-15",
                "horas": 0,
            },
            content_type="application/json",
        )
        .will_respond_with(400)
        .with_body(
            {
                "error": "HORAS_INVALIDAS",
                "mensaje": match.str("La cantidad de horas debe ser mayor a cero"),
            },
            content_type="application/json",
        )
    )

    yield pact
    pact.write_file(PACTS_DIR, overwrite=True)


@pytest.fixture(scope="module")
def cliente(pact: Pact) -> Generator[ReservasClient, None, None]:
    # Ambas interacciones se definen antes de levantar el mock server, y una
    # unica sesion de `pact.serve()` (compartida por los tests del modulo) las
    # ejercita a las dos: pact-python 3.4 no admite agregar o modificar
    # interacciones sobre el mismo handle despues de una sesion de `serve()`.
    with pact.serve() as srv:
        yield ReservasClient(str(srv.url))


def test_reserva_valida(cliente: ReservasClient) -> None:
    reserva = cliente.crear_reserva(
        usuario_id="U100", sala="SALA-1", fecha="2026-09-15", horas=2
    )

    assert reserva["id"]
    assert reserva["estado"] == "ACTIVA"


def test_reserva_invalida_por_horas(cliente: ReservasClient) -> None:
    with pytest.raises(HorasInvalidasError):
        cliente.crear_reserva(
            usuario_id="U100", sala="SALA-1", fecha="2026-09-15", horas=0
        )
