import os

from fastapi import FastAPI

from services.reservas.app.provider_states import router as provider_states_router
from services.reservas.app.routers import router


def create_app() -> FastAPI:
    _app = FastAPI(title="Servicio de Reservas")
    _app.include_router(router)
    if os.environ.get("PACT_STATES_ENABLED") == "1":
        _app.include_router(provider_states_router)
    return _app


app = create_app()