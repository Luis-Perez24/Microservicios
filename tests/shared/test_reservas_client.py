import json

import httpx
import pytest

from shared.reservas_client import HorasInvalidasError, ReservasClient


def cliente_con(handler) -> ReservasClient:
    """Construye un ReservasClient cuyo transporte es un MockTransport."""
    return ReservasClient(
        "http://reservas.test", transport=httpx.MockTransport(handler)
    )


def test_crear_reserva_envia_post_y_devuelve_201():
    enviado: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        enviado["metodo"] = request.method
        enviado["ruta"] = request.url.path
        enviado["cuerpo"] = json.loads(request.content)
        return httpx.Response(
            201,
            json={
                "id": "R-1001",
                "usuarioId": "U100",
                "sala": "SALA-1",
                "fecha": "2026-09-15",
                "horas": 2,
                "estado": "ACTIVA",
            },
        )

    resultado = cliente_con(handler).crear_reserva(
        "U100", "SALA-1", "2026-09-15", 2
    )

    assert enviado["metodo"] == "POST"
    assert enviado["ruta"] == "/reservas"
    assert enviado["cuerpo"] == {
        "usuarioId": "U100",
        "sala": "SALA-1",
        "fecha": "2026-09-15",
        "horas": 2,
    }
    assert resultado["id"] == "R-1001"
    assert resultado["estado"] == "ACTIVA"


def test_crear_reserva_400_horas_invalidas_lanza_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": "HORAS_INVALIDAS",
                "mensaje": "La cantidad de horas debe ser mayor a cero",
            },
        )

    client = cliente_con(handler)

    with pytest.raises(HorasInvalidasError) as exc:
        client.crear_reserva("U100", "SALA-1", "2026-09-15", 0)

    assert exc.value.mensaje == "La cantidad de horas debe ser mayor a cero"


def test_error_distinto_se_propaga_como_http_status_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "INTERNO", "mensaje": "fallo"})

    client = cliente_con(handler)

    with pytest.raises(httpx.HTTPStatusError):
        client.crear_reserva("U100", "SALA-1", "2026-09-15", 2)


def test_reservas_de_usuario_con_elementos():
    enviado: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        enviado["metodo"] = request.method
        enviado["ruta"] = request.url.path
        enviado["query"] = dict(request.url.params)
        return httpx.Response(
            200,
            json=[
                {
                    "id": "R-1001",
                    "usuarioId": "U100",
                    "sala": "SALA-1",
                    "fecha": "2026-09-15",
                    "horas": 2,
                    "estado": "ACTIVA",
                }
            ],
        )

    resultado = cliente_con(handler).reservas_de_usuario("U100")

    assert enviado["metodo"] == "GET"
    assert enviado["ruta"] == "/reservas"
    assert enviado["query"] == {"usuarioId": "U100"}
    assert resultado[0]["id"] == "R-1001"


def test_reservas_de_usuario_lista_vacia():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    resultado = cliente_con(handler).reservas_de_usuario("U200")

    assert resultado == []


def test_verificar_reserva_valida():
    enviado: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        enviado["metodo"] = request.method
        enviado["ruta"] = request.url.path
        return httpx.Response(200, json={"reservaId": "R-1001", "valida": True})

    resultado = cliente_con(handler).verificar_reserva("R-1001")

    assert enviado["metodo"] == "GET"
    assert enviado["ruta"] == "/reservas/R-1001/verificacion"
    assert resultado == {"reservaId": "R-1001", "valida": True}


def test_verificar_reserva_no_valida():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"reservaId": "R-9999", "valida": False})

    resultado = cliente_con(handler).verificar_reserva("R-9999")

    assert resultado == {"reservaId": "R-9999", "valida": False}
