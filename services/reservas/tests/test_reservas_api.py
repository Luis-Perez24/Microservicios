import pytest
from fastapi.testclient import TestClient

from services.reservas.app import repository
from services.reservas.app.main import app


@pytest.fixture(autouse=True)
def repositorio_limpio():
    repository.reset()
    yield
    repository.reset()


@pytest.fixture()
def cliente() -> TestClient:
    return TestClient(app)


def test_crear_reserva_devuelve_201_con_campos_camelcase(cliente):
    respuesta = cliente.post(
        "/reservas",
        json={
            "usuarioId": "U100",
            "sala": "SALA-1",
            "fecha": "2026-09-15",
            "horas": 2,
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "id": "R-1001",
        "usuarioId": "U100",
        "sala": "SALA-1",
        "fecha": "2026-09-15",
        "horas": 2,
        "estado": "ACTIVA",
    }


def test_crear_reserva_con_horas_cero_devuelve_400(cliente):
    respuesta = cliente.post(
        "/reservas",
        json={
            "usuarioId": "U100",
            "sala": "SALA-1",
            "fecha": "2026-09-15",
            "horas": 0,
        },
    )

    assert respuesta.status_code == 400
    assert respuesta.json() == {
        "error": "HORAS_INVALIDAS",
        "mensaje": "La cantidad de horas debe ser mayor a cero",
    }


def test_reservas_de_usuario_con_elementos(cliente):
    cliente.post(
        "/reservas",
        json={
            "usuarioId": "U100",
            "sala": "SALA-1",
            "fecha": "2026-09-15",
            "horas": 2,
        },
    )

    respuesta = cliente.get("/reservas", params={"usuarioId": "U100"})

    assert respuesta.status_code == 200
    assert respuesta.json() == [
        {
            "id": "R-1001",
            "usuarioId": "U100",
            "sala": "SALA-1",
            "fecha": "2026-09-15",
            "horas": 2,
            "estado": "ACTIVA",
        }
    ]


def test_reservas_de_usuario_sin_elementos_devuelve_lista_vacia(cliente):
    respuesta = cliente.get("/reservas", params={"usuarioId": "U200"})

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_verificar_reserva_existente_y_activa(cliente):
    cliente.post(
        "/reservas",
        json={
            "usuarioId": "U100",
            "sala": "SALA-1",
            "fecha": "2026-09-15",
            "horas": 2,
        },
    )

    respuesta = cliente.get("/reservas/R-1001/verificacion")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"reservaId": "R-1001", "valida": True}


def test_verificar_reserva_inexistente_devuelve_valida_false(cliente):
    respuesta = cliente.get("/reservas/R-9999/verificacion")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"reservaId": "R-9999", "valida": False}