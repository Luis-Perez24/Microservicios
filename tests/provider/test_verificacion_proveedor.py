from pathlib import Path

import pytest
from pact import Verifier

PACTS_DIR = Path(__file__).resolve().parents[2] / "pacts"


@pytest.mark.proveedor
def test_verificacion_de_contratos() -> None:
    verifier = (
        Verifier("ServicioReservas")
        .add_transport(url="http://localhost:8001")
        .add_source(str(PACTS_DIR))
        .state_handler("http://localhost:8001/_pact/provider-states", body=True)
    )

    resultado = verifier.verify()

    assert resultado