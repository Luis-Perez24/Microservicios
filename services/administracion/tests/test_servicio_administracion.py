# services/administracion/tests/test_servicio_administracion.py
from collections.abc import Iterator
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient

from services.administracion.app import main
from shared.reservas_client import ReservasClient


@pytest.fixture
def api() -> Iterator[tuple[TestClient, Mock]]:
    handler = Mock()
    cliente = ReservasClient(
        "http://reservas.test", transport=httpx.MockTransport(handler)
    )
    main.app.dependency_overrides[main.get_reservas_client] = lambda: cliente
    try:
        with TestClient(main.app) as test_client:
            yield test_client, handler
    finally:
        main.app.dependency_overrides.pop(main.get_reservas_client)
        cliente._client.close()


@pytest.mark.parametrize(
    ("reserva_id", "valida"),
    [("R-1001", True), ("R-9999", False), ("R-1001", False)],
    ids=["activa", "inexistente", "inactiva"],
)
def test_administracion_valida_reserva(api, reserva_id, valida):
    cliente, handler = api
    resultado = {"reservaId": reserva_id, "valida": valida}
    handler.return_value = httpx.Response(200, json=resultado)

    respuesta = cliente.get(f"/admin/reservas/{reserva_id}/validacion")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "application/json"
    assert respuesta.json() == resultado
    handler.assert_called_once()
    solicitud = handler.call_args.args[0]
    assert solicitud.method == "GET"
    assert solicitud.url.path == f"/reservas/{reserva_id}/verificacion"
    assert not solicitud.url.query


@pytest.mark.parametrize("error", [httpx.ConnectError, httpx.ReadTimeout])
def test_administracion_proveedor_no_responde(api, error):
    cliente, handler = api
    handler.side_effect = error("detalle interno")

    respuesta = cliente.get("/admin/reservas/R-1001/validacion")

    assert respuesta.status_code == 502
    assert respuesta.json() == {
        "error": "RESERVAS_NO_DISPONIBLE",
        "mensaje": "No se pudo consultar el Servicio de Reservas",
    }


@pytest.mark.parametrize("status", [404, 500, 503])
def test_administracion_error_http_no_se_convierte_en_valida_false(api, status):
    cliente, handler = api
    handler.return_value = httpx.Response(status, json={"error": "interno"})

    respuesta = cliente.get("/admin/reservas/R-9999/validacion")

    assert respuesta.status_code == 502
    assert respuesta.json()["error"] == "RESERVAS_NO_DISPONIBLE"


@pytest.mark.parametrize(
    "cuerpo",
    [
        [],
        {"reservaId": "R-1001"},
        {"reservaId": "R-1001", "valida": "false"},
        {"reservaId": "R-1001", "valida": 1},
        {"reservaId": "R-9999", "valida": True},
    ],
)
def test_administracion_rechaza_respuesta_incompatible(api, cuerpo):
    cliente, handler = api
    handler.return_value = httpx.Response(200, json=cuerpo)

    respuesta = cliente.get("/admin/reservas/R-1001/validacion")

    assert respuesta.status_code == 502
    assert respuesta.json()["error"] == "RESERVAS_NO_DISPONIBLE"


def test_administracion_rechaza_json_invalido(api):
    cliente, handler = api
    handler.return_value = httpx.Response(200, text="<html>error</html>")

    assert cliente.get("/admin/reservas/R-1001/validacion").status_code == 502


@pytest.mark.parametrize("url", [None, "http://reservas.configurada:9000"])
def test_administracion_configura_url_y_cierra_cliente(monkeypatch, url):
    if url is None:
        monkeypatch.delenv("RESERVAS_URL", raising=False)
    else:
        monkeypatch.setenv("RESERVAS_URL", url)
    esperado = url or "http://localhost:8001"

    with TestClient(main.app):
        cliente = main.app.state.reservas_client
        assert str(cliente._client.base_url) == esperado
        assert not cliente._client.is_closed

    assert cliente._client.is_closed
