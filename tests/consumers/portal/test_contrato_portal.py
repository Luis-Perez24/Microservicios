# tests/consumers/portal/test_contrato_portal.py
from pathlib import Path

import pytest
from pact import Pact, match

from shared.reservas_client import ReservasClient

PACTS_DIR = Path(__file__).resolve().parents[3] / "pacts"
RESERVA = {
    "id": "R-1001",
    "usuarioId": "U100",
    "sala": "SALA-1",
    "fecha": "2026-09-15",
    "horas": 2,
    "estado": "ACTIVA",
}


@pytest.fixture(scope="module")
def pact() -> Pact:
    contrato = Pact("PortalUsuario", "ServicioReservas").with_specification("V4")
    (
        contrato.upon_receiving("una consulta de reservas del usuario U100")
        .given("el usuario U100 tiene una reserva activa")
        .with_request("GET", "/reservas")
        .with_query_parameter("usuarioId", "U100")
        .will_respond_with(200)
        .with_body(
            match.each_like(
                {
                    "id": match.regex("R-1001", regex=r"^R-\d+$"),
                    "usuarioId": match.regex("U100", regex=r"^U100$"),
                    "sala": match.regex("SALA-1", regex=r"^SALA-\d+$"),
                    "fecha": match.date("2026-09-15"),
                    "horas": match.int(2),
                    "estado": match.regex("ACTIVA", regex=r"^ACTIVA$"),
                },
                min=1,
            ),
            content_type="application/json",
        )
    )
    (
        contrato.upon_receiving("una consulta de reservas del usuario U200")
        .given("el usuario U200 no tiene reservas")
        .with_request("GET", "/reservas")
        .with_query_parameter("usuarioId", "U200")
        .will_respond_with(200)
        .with_body([], content_type="application/json")
    )
    return contrato


def test_contrato_portal_con_y_sin_reservas(pact: Pact) -> None:
    # Una sesion ejercita ambos estados; no publica un Pact parcial si falla.
    with pact.serve() as srv:
        cliente = ReservasClient(str(srv.url))
        try:
            assert cliente.reservas_de_usuario("U100") == [RESERVA]
            assert cliente.reservas_de_usuario("U200") == []
        finally:
            cliente._client.close()

    # Solo se escribe despues de que las aserciones y el mock se verifican.
    PACTS_DIR.mkdir(parents=True, exist_ok=True)
    pact.write_file(PACTS_DIR, overwrite=True)
