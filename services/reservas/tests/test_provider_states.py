import pytest
from fastapi.testclient import TestClient

from services.reservas.app import repository
from services.reservas.app.main import create_app

ESTADO_U100_ACTIVA = "el usuario U100 tiene una reserva activa"
ESTADO_U200_VACIO = "el usuario U200 no tiene reservas"
ESTADO_R1001_EXISTE = "la reserva R-1001 existe y esta activa"
ESTADO_R9999_NO_EXISTE = "la reserva R-9999 no existe"
ESTADO_ACEPTA_NUEVAS = "el sistema acepta nuevas reservas"

CUERPO_SETUP = {
    "state": ESTADO_U100_ACTIVA,
    "params": {},
    "action": "setup",
}


@pytest.fixture(autouse=True)
def repositorio_limpio():
    repository.reset()
    yield
    repository.reset()


@pytest.fixture()
def cliente_con_states(monkeypatch) -> TestClient:
    monkeypatch.setenv("PACT_STATES_ENABLED", "1")
    return TestClient(create_app())


def aplicar_estado(cliente: TestClient, estado: str) -> None:
    respuesta = cliente.post(
        "/_pact/provider-states",
        json={"state": estado, "params": {}, "action": "setup"},
    )
    assert respuesta.status_code == 200


def test_el_usuario_u100_tiene_una_reserva_activa(cliente_con_states):
    aplicar_estado(cliente_con_states, ESTADO_U100_ACTIVA)

    reservas = cliente_con_states.get(
        "/reservas", params={"usuarioId": "U100"}
    ).json()
    assert [r["id"] for r in reservas] == ["R-1001"]
    assert reservas[0]["estado"] == "ACTIVA"
    assert cliente_con_states.get(
        "/reservas", params={"usuarioId": "U200"}
    ).json() == []


def test_el_usuario_u200_no_tiene_reservas(cliente_con_states):
    aplicar_estado(cliente_con_states, ESTADO_U200_VACIO)

    assert cliente_con_states.get(
        "/reservas", params={"usuarioId": "U200"}
    ).json() == []
    assert repository.obtener("R-1001") is None


def test_la_reserva_r1001_existe_y_esta_activa(cliente_con_states):
    aplicar_estado(cliente_con_states, ESTADO_R1001_EXISTE)

    verificacion = cliente_con_states.get("/reservas/R-1001/verificacion").json()
    assert verificacion == {"reservaId": "R-1001", "valida": True}


def test_la_reserva_r9999_no_existe(cliente_con_states):
    aplicar_estado(cliente_con_states, ESTADO_R9999_NO_EXISTE)

    verificacion = cliente_con_states.get("/reservas/R-9999/verificacion").json()
    assert verificacion == {"reservaId": "R-9999", "valida": False}


def test_el_sistema_acepta_nuevas_reservas(cliente_con_states):
    aplicar_estado(cliente_con_states, ESTADO_ACEPTA_NUEVAS)

    creada = cliente_con_states.post(
        "/reservas",
        json={
            "usuarioId": "U100",
            "sala": "SALA-1",
            "fecha": "2026-09-15",
            "horas": 2,
        },
    ).json()
    assert creada["id"] == "R-1001"


def test_estado_desconocido_devuelve_400(cliente_con_states):
    respuesta = cliente_con_states.post(
        "/_pact/provider-states",
        json={
            "state": "un estado inventado",
            "params": {},
            "action": "setup",
        },
    )

    assert respuesta.status_code == 400
    assert respuesta.json() == {
        "error": "ESTADO_DESCONOCIDO",
        "mensaje": "un estado inventado",
    }


def test_action_distinta_de_setup_no_hace_nada(cliente_con_states):
    aplicar_estado(cliente_con_states, ESTADO_U100_ACTIVA)

    respuesta = cliente_con_states.post(
        "/_pact/provider-states",
        json={
            "state": ESTADO_R9999_NO_EXISTE,
            "params": {},
            "action": "teardown",
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {}
    assert repository.obtener("R-1001") is not None


def test_endpoint_no_montado_sin_pact_states_enabled(monkeypatch):
    monkeypatch.delenv("PACT_STATES_ENABLED", raising=False)
    cliente = TestClient(create_app())

    respuesta = cliente.post(
        "/_pact/provider-states",
        json=CUERPO_SETUP,
    )

    assert respuesta.status_code == 404