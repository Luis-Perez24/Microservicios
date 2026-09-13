# Contrato de API — Sistema de Reservas de Salas

Acuerdo técnico del equipo. Todo lo que aparece aquí se escribe **exactamente igual** en
el código de consumidores y proveedor. Si algo necesita cambiar, se avisa al grupo y se
actualiza este documento **antes** de tocar el código.

---

## 1. Stack y versiones

| Componente | Versión |
|---|---|
| Python | 3.12 |
| FastAPI + Uvicorn | última estable |
| Cliente HTTP | `httpx` |
| Pruebas | `pytest` |
| Pact | `pact-python~=3.4` (API v3: `from pact import Pact, Verifier, match`) |
| Especificación Pact | `V4` |

No usar `pact.v2` ni ejemplos de tutoriales antiguos (`Consumer(...).has_pact_with(...)`).

Entorno local (una vez, desde la raíz):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

---

## 2. Nombres de pacticipants

| Rol | Nombre exacto | Archivo generado |
|---|---|---|
| Proveedor | `ServicioReservas` | — |
| Consumidor (Contrato 1) | `AplicacionReserva` | `pacts/AplicacionReserva-ServicioReservas.json` |
| Consumidor (Contrato 2) | `PortalUsuario` | `pacts/PortalUsuario-ServicioReservas.json` |
| Consumidor (Contrato 3) | `ServicioAdministracion` | `pacts/ServicioAdministracion-ServicioReservas.json` |

---

## 3. Modelo `Reserva`

Campos en **camelCase** en todos los JSON.

| Campo | Tipo | Formato / valores | Ejemplo |
|---|---|---|---|
| `id` | string | `R-` + número (`^R-\d+$`) | `"R-1001"` |
| `usuarioId` | string | `U` + número | `"U100"` |
| `sala` | string | `SALA-` + número | `"SALA-1"` |
| `fecha` | string | ISO 8601 `YYYY-MM-DD` | `"2026-09-15"` |
| `horas` | integer | entero `> 0` | `2` |
| `estado` | string | `"ACTIVA"` \| `"CANCELADA"` | `"ACTIVA"` |

Formato único de error:

```json
{ "error": "CODIGO_EN_MAYUSCULAS", "mensaje": "Texto legible" }
```

---

## 4. Endpoints del Servicio de Reservas

Todas las respuestas llevan `Content-Type: application/json`.

### 4.1 Crear reserva — Contrato 1

`POST /reservas`

Request:
```json
{ "usuarioId": "U100", "sala": "SALA-1", "fecha": "2026-09-15", "horas": 2 }
```

**201 Created**:
```json
{ "id": "R-1001", "usuarioId": "U100", "sala": "SALA-1", "fecha": "2026-09-15", "horas": 2, "estado": "ACTIVA" }
```

**400 Bad Request** (si `horas <= 0`):
```json
{ "error": "HORAS_INVALIDAS", "mensaje": "La cantidad de horas debe ser mayor a cero" }
```

> ⚠️ Proveedor: validar `horas` a mano y devolver **400**. Si se usa `Field(gt=0)` de
> Pydantic, FastAPI responde **422** y el contrato falla.

### 4.2 Consultar reservas de un usuario — Contrato 2

`GET /reservas?usuarioId=U100`

**200 OK** con reservas:
```json
[ { "id": "R-1001", "usuarioId": "U100", "sala": "SALA-1", "fecha": "2026-09-15", "horas": 2, "estado": "ACTIVA" } ]
```

**200 OK** sin reservas (`usuarioId=U200`):
```json
[]
```

Un usuario sin reservas **no es error**: nunca 404.

### 4.3 Verificar una reserva — Contrato 3

`GET /reservas/{reservaId}/verificacion`

**200 OK** si existe y está activa:
```json
{ "reservaId": "R-1001", "valida": true }
```

**200 OK** si no existe (o no está activa):
```json
{ "reservaId": "R-9999", "valida": false }
```

Una reserva inexistente **no es error**: nunca 404.

---

## 5. Provider states

Los nombres van **sin tildes** a propósito, para evitar diferencias de codificación al
copiarlos. Se copian y pegan desde aquí; nunca se escriben a mano.

| # | Nombre exacto (`given(...)`) | Datos que deja el proveedor | Lo usa |
|---|---|---|---|
| 1 | `el usuario U100 tiene una reserva activa` | Solo `R-1001` (U100, SALA-1, 2026-09-15, 2 h, ACTIVA) | Contrato 2 |
| 2 | `el usuario U200 no tiene reservas` | Repositorio vacío | Contrato 2 |
| 3 | `la reserva R-1001 existe y esta activa` | Solo `R-1001` (mismos datos que el estado 1) | Contrato 3 |
| 4 | `la reserva R-9999 no existe` | Repositorio vacío | Contrato 3 |
| 5 | `el sistema acepta nuevas reservas` | Repositorio vacío | Contrato 1 (válida e inválida) |

Cada estado **primero ejecuta `reset()`** y luego siembra solo lo indicado.

### Endpoint de estados (solo proveedor)

`POST /_pact/provider-states`: se monta **solo** si la variable `PACT_STATES_ENABLED=1`.

Request enviado por el Verifier:
```json
{ "state": "el usuario U100 tiene una reserva activa", "params": {}, "action": "setup" }
```

- Estado conocido → `200 {}`.
- Estado desconocido → `400 {"error": "ESTADO_DESCONOCIDO", "mensaje": "<nombre recibido>"}`.
- `action` distinto de `"setup"` → `200 {}` sin hacer nada.

---

## 6. Interfaces compartidas entre integrantes

### 6.1 Cliente HTTP — `shared/reservas_client.py`

```python
class HorasInvalidasError(Exception):
    """Se lanza cuando el proveedor responde 400 HORAS_INVALIDAS."""

class ReservasClient:
    def __init__(self, base_url: str, timeout: float = 5.0, transport: httpx.BaseTransport | None = None) -> None: ...
    def crear_reserva(self, usuario_id: str, sala: str, fecha: str, horas: int) -> dict: ...
    def reservas_de_usuario(self, usuario_id: str) -> list[dict]: ...
    def verificar_reserva(self, reserva_id: str) -> dict: ...  # {"reservaId", "valida"}
```

- Parámetros Python en `snake_case`; JSON en `camelCase`.
- Otros códigos de error → `httpx.HTTPStatusError` (vía `raise_for_status()`).
- La URL base **siempre** se recibe por parámetro (los tests pasan la del mock de Pact).

### 6.2 Repositorio del proveedor — `services/reservas/app/repository.py`

```python
def reset() -> None: ...
def seed(reserva: Reserva) -> None: ...
def guardar(usuario_id: str, sala: str, fecha: str, horas: int) -> Reserva: ...
def listar_por_usuario(usuario_id: str) -> list[Reserva]: ...
def obtener(reserva_id: str) -> Reserva | None: ...
```

Id generado: `R-` + (mayor número existente, o 1000 si no hay reservas) + 1.

### 6.3 Servicios consumidores (no forman parte de Pact)

| Servicio | Endpoint | Respuesta 200 |
|---|---|---|
| Portal de Usuario | `GET /portal/usuarios/{usuarioId}/reservas` | `{"usuarioId": "U100", "reservas": [ ... ]}` |
| Administración | `GET /admin/reservas/{reservaId}/validacion` | `{"reservaId": "R-1001", "valida": true}` |

- Ambos leen la URL del proveedor desde la variable `RESERVAS_URL` (por defecto `http://localhost:8001`).
- Si el proveedor no responde → `502 {"error": "RESERVAS_NO_DISPONIBLE", "mensaje": "..."}`.

---

## 7. Cómo escribir los tests de consumidor

- Una fixture `Pact("<Consumidor>", "ServicioReservas").with_specification("V4")` por
  consumidor, con `scope="module"`.
- Al terminar: `pact.write_file(PACTS_DIR, overwrite=True)`, con
  `PACTS_DIR = Path(__file__).resolve().parents[3] / "pacts"`.
- Cada interacción usa `.given("<estado exacto de la sección 5>")`.
- El cliente se construye con la URL del mock: `with pact.serve() as srv: ReservasClient(str(srv.url))`.
- Valores generados por el proveedor se validan con matchers, no con literales:
  - `id` en la creación → `match.regex("R-1001", regex=r"^R-\d+$")`
  - lista de U100 → `match.each_like({...}, min=1)`
- Lista vacía de U200 → literal `[]`.
- Query string → `.with_query_parameter("usuarioId", "U100")`.

## 8. Cómo verifica el proveedor

Test marcado con `@pytest.mark.proveedor` (se excluye de la suite normal porque necesita
el proveedor levantado):

```python
Verifier("ServicioReservas")
    .add_transport(url="http://localhost:8001")
    .add_source("pacts/")
    .state_handler("http://localhost:8001/_pact/provider-states", body=True)
    .verify()
```

---

## 9. Estructura y convenciones del repositorio

```
Microservicios/
├── docs/api-contract.md
├── docker-compose.yml
├── .dockerignore
├── pytest.ini                      # pythonpath = . · marker "proveedor"
├── requirements-dev.txt
├── bin/generar-contratos.sh
├── bin/verificar-proveedor.sh
├── pacts/                          # solo generados
├── shared/__init__.py
├── shared/reservas_client.py
├── services/__init__.py
├── services/reservas/              # __init__.py, Dockerfile, requirements.txt
│   ├── app/                        # __init__.py, main.py, models.py, repository.py, routers.py, provider_states.py
│   └── tests/
├── services/portal_usuario/        # __init__.py, Dockerfile, requirements.txt, app/, tests/
├── services/administracion/        # __init__.py, Dockerfile, requirements.txt, app/, tests/
├── tests/shared/test_reservas_client.py
├── tests/consumers/app_reserva/test_contrato_app_reserva.py
├── tests/consumers/portal/test_contrato_portal.py
├── tests/consumers/administracion/test_contrato_administracion.py
└── tests/provider/test_verificacion_proveedor.py
```

- Carpetas en `snake_case` (sin guiones) para que sean importables:
  `from services.reservas.app.main import app`, `from shared.reservas_client import ReservasClient`.
- Nombres de archivos de test **únicos** en todo el repo.
- `pytest` se ejecuta siempre desde la raíz.
- `requirements.txt` por servicio (lo que usa su contenedor) y `requirements-dev.txt` en la raíz (desarrollo y pruebas).

### Puertos y Docker

| Servicio | Nombre en compose | Puerto interno | Puerto host |
|---|---|---|---|
| Reservas | `reservas` | 8000 | 8001 |
| Portal de Usuario | `portal` | 8000 | 8002 |
| Administración | `administracion` | 8000 | 8003 |

- `build.context: .` (raíz), porque Portal y Administración copian `shared/`.
- Dentro del contenedor: `WORKDIR /srv` y `uvicorn services.<servicio>.app.main:app --host 0.0.0.0 --port 8000`.
- `reservas` con `PACT_STATES_ENABLED=1`.
- `portal` y `administracion` con `RESERVAS_URL=http://reservas:8000`.

### Git (git flow)

| Rama | Uso |
|---|---|
| `main` | Solo versiones entregadas, con tag (`v1.0.0`). Nadie commitea directo. |
| `develop` | Integración. Se llega solo por PR. |
| `feature/<nombre>` | Trabajo de cada integrante (ej. `feature/luis`); nace de `develop` y vuelve por PR. |
| `release/<versión>` | Preparación de la entrega; se mergea a `main` (con tag) y a `develop`. |
| `hotfix/<tema>` | Corrección urgente sobre `main`. |

- PR hacia `develop` revisado por otra persona; merge con `--no-ff`.
- Commits con prefijo: `feat:`, `test:`, `fix:`, `docs:`, `build:`, `chore:`.
- Cada uno modifica solo sus archivos; si necesita cambiar uno ajeno, lo pide por el grupo.
- `pacts/*.json` **nunca se editan a mano**: si algo falla, se corrige el test y se regeneran.
