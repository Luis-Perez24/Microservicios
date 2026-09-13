import httpx


class HorasInvalidasError(Exception):
    """Se lanza cuando el proveedor responde 400 HORAS_INVALIDAS."""

    def __init__(self, mensaje: str) -> None:
        self.mensaje: str = mensaje
        super().__init__(mensaje)


class ReservasClient:
    """Cliente HTTP del Servicio de Reservas."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        # transport solo existe para las pruebas (httpx.MockTransport).
        self._client = httpx.Client(
            base_url=base_url, timeout=timeout, transport=transport
        )

    def crear_reserva(
        self, usuario_id: str, sala: str, fecha: str, horas: int
    ) -> dict:
        respuesta = self._client.post(
            "/reservas",
            json={
                "usuarioId": usuario_id,
                "sala": sala,
                "fecha": fecha,
                "horas": horas,
            },
        )
        if respuesta.status_code == 400:
            cuerpo = respuesta.json()
            if cuerpo.get("error") == "HORAS_INVALIDAS":
                raise HorasInvalidasError(cuerpo.get("mensaje", ""))
        respuesta.raise_for_status()
        return respuesta.json()

    def reservas_de_usuario(self, usuario_id: str) -> list[dict]:
        respuesta = self._client.get("/reservas", params={"usuarioId": usuario_id})
        respuesta.raise_for_status()
        return respuesta.json()

    def verificar_reserva(self, reserva_id: str) -> dict:
        respuesta = self._client.get(f"/reservas/{reserva_id}/verificacion")
        respuesta.raise_for_status()
        return respuesta.json()
