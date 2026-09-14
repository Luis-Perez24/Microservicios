# Microservicios — Sistema de Reservas de Salas

Pruebas de contrato con **Pact** entre un proveedor (`ServicioReservas`) y tres
consumidores (`AplicacionReserva`, `PortalUsuario` y `ServicioAdministracion`).
Todo el acuerdo técnico vive en [`docs/api-contract.md`](docs/api-contract.md) y
**no se modifica nada fuera de lo que ahí aparece**.

## Integrantes

- Félix Santana
- Luis Pérez
- Jun Sáez
- Felipe Seguel
- Sebastián Vidal
- Orlando Caullan

## Stack

| Componente | Versión |
|---|---|
| Python | 3.12 |
| FastAPI + Uvicorn | última estable |
| Cliente HTTP | `httpx` |
| Pruebas | `pytest` |
| Pact | `pact-python~=3.4` (especificación `V4`) |

## Puesta en marcha

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

`pytest` se ejecuta siempre desde la raíz.

## Estructura

```
├── docs/api-contract.md        # el contrato: endpoints, JSON, estados, convenciones
├── docker-compose.yml          # reservas (8001), portal (8002), administracion (8003)
├── bin/
│   ├── generar-contratos.sh    # genera los pacts en ./pacts desde tests/consumers
│   └── verificar-proveedor.sh  # levanta el proveedor y corre la verificacion Pact
├── pacts/                      # contratos generados (nunca se editan a mano)
├── shared/reservas_client.py   # cliente HTTP consumido por los servicios
├── services/
│   ├── reservas/               # proveedor: app/ + tests/ + Dockerfile
│   ├── portal_usuario/         # consumidor (contrato 2)
│   └── administracion/         # consumidor (contrato 3)
└── tests/
    ├── shared/                 # tests del cliente con httpx.MockTransport
    ├── consumers/              # tests de contrato: generan los pacts
    └── provider/               # Verifier (@pytest.mark.proveedor)
```

## Contratos

```bash
# 1. Generar los pacts en ./pacts (requiere el venv)
bin/generar-contratos.sh

# 2. Verificar que el proveedor cumple los contratos
#    (levanta el Servicio de Reservas en http://localhost:8001 y corre la verificacion)
bin/verificar-proveedor.sh
```

La suite normal de desarrollo excluye la verificacion (necesita el proveedor
levantado):

```bash
.venv/bin/pytest -m "not proveedor"
```

Los pacts se generan codificando matchers, no valores literales. Si un contrato
falla, se corrige el test de consumidor y se regenera el pact; `pacts/*.json`
**nunca** se editan a mano.

## Servicios (docker compose)

| Servicio | Nombre en compose | Puerto host |
|---|---|---|
| Reservas | `reservas` | 8001 |
| Portal de Usuario | `portal` | 8002 |
| Administración | `administracion` | 8003 |

Todos hacen `build.context: .` desde la raíz. `reservas` corre con
`PACT_STATES_ENABLED=1` para exponer `POST /_pact/provider-states`; `portal` y
`administracion` apuntan al proveedor con `RESERVAS_URL=http://reservas:8000`.

```bash
docker compose up --build
```

Los `Dockerfile` de `portal_usuario` y `administracion` son responsabilidad de
sus dueños; el compose ya los referencia.


Cada uno modifica solo sus archivos; si necesita tocar uno ajeno, lo pide por el
grupo.
