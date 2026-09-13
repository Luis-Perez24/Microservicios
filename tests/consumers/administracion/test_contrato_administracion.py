from collections.abc import Generator
from pathlib import Path

import pytest
from pact import Pact

from shared.reservas_client import ReservasClient

PACTS_DIR = Path(__file__).resolve().parents[3] / "pacts"


@pytest.fixture(scope="module")
def pact() -> Generator[Pact, None, None]:
    pact = Pact("ServicioAdministracion", "ServicioReservas").with_specification("V4")

    (
        pact.upon_receiving("una verificacion de una reserva existente y activa")
        .given("la reserva R-1001 existe y esta activa")
        .with_request("GET", "/reservas/R-1001/verificacion")
        .will_respond_with(200)
        .with_body(
            {"reservaId": "R-1001", "valida": True},
            content_type="application/json",
        )
    )
    (
        pact.upon_receiving("una verificacion de una reserva inexistente")
        .given("la reserva R-9999 no existe")
        .with_request("GET", "/reservas/R-9999/verificacion")
        .will_respond_with(200)
        .with_body(
            {"reservaId": "R-9999", "valida": False},
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


def test_reserva_existente_y_activa(cliente: ReservasClient) -> None:
    resultado = cliente.verificar_reserva("R-1001")

    assert resultado["valida"] is True


def test_reserva_inexistente(cliente: ReservasClient) -> None:
    resultado = cliente.verificar_reserva("R-9999")

    assert resultado["valida"] is False
