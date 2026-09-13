# services/portal_usuario/tests/test_portal_usuario.py
from collections.abc import Iterator
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient

from services.portal_usuario.app import main
from shared.reservas_client import ReservasClient

RESERVA = {
    "id": "R-1001",
    "usuarioId": "U100",
    "sala": "SALA-1",
    "fecha": "2026-09-15",
    "horas": 2,
    "estado": "ACTIVA",
}


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
    ("usuario_id", "reservas"),
    [
        ("U100", [RESERVA]),
        ("U200", []),
        ("U100", [RESERVA, {**RESERVA, "id": "R-1002", "estado": "CANCELADA"}]),
    ],
)
def test_portal_consulta_reservas(api, usuario_id, reservas):
    cliente, handler = api
    handler.return_value = httpx.Response(200, json=reservas)

    respuesta = cliente.get(f"/portal/usuarios/{usuario_id}/reservas")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "application/json"
    assert respuesta.json() == {"usuarioId": usuario_id, "reservas": reservas}
    handler.assert_called_once()
    solicitud = handler.call_args.args[0]
    assert solicitud.method == "GET"
    assert solicitud.url.path == "/reservas"
    assert dict(solicitud.url.params) == {"usuarioId": usuario_id}


@pytest.mark.parametrize("error", [httpx.ConnectError, httpx.ReadTimeout])
def test_portal_proveedor_no_responde(api, error):
    cliente, handler = api
    handler.side_effect = error("detalle interno")

    respuesta = cliente.get("/portal/usuarios/U100/reservas")

    assert respuesta.status_code == 502
    assert respuesta.json() == {
        "error": "RESERVAS_NO_DISPONIBLE",
        "mensaje": "No se pudo consultar el Servicio de Reservas",
    }


@pytest.mark.parametrize("status", [404, 500, 503])
def test_portal_error_http_no_se_convierte_en_lista_vacia(api, status):
    cliente, handler = api
    handler.return_value = httpx.Response(status, json={"error": "interno"})

    respuesta = cliente.get("/portal/usuarios/U200/reservas")

    assert respuesta.status_code == 502
    assert respuesta.json()["error"] == "RESERVAS_NO_DISPONIBLE"


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        [{"id": "R-1001"}],
        [{**RESERVA, "horas": 0}],
        [{**RESERVA, "fecha": "2026-02-30"}],
        [{**RESERVA, "usuarioId": "U200"}],
    ],
)
def test_portal_rechaza_respuesta_incompatible(api, cuerpo):
    cliente, handler = api
    handler.return_value = httpx.Response(200, json=cuerpo)

    respuesta = cliente.get("/portal/usuarios/U100/reservas")

    assert respuesta.status_code == 502
    assert respuesta.json()["error"] == "RESERVAS_NO_DISPONIBLE"


def test_portal_rechaza_json_invalido(api):
    cliente, handler = api
    handler.return_value = httpx.Response(200, text="<html>error</html>")

    assert cliente.get("/portal/usuarios/U100/reservas").status_code == 502


@pytest.mark.parametrize("url", [None, "http://reservas.configurada:9000"])
def test_portal_configura_url_y_cierra_cliente(monkeypatch, url):
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
