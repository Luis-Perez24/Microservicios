import pytest

from services.reservas.app.models import Reserva
from services.reservas.app import repository


@pytest.fixture(autouse=True)
def repositorio_limpio():
    repository.reset()
    yield
    repository.reset()


def test_reset_deja_el_repositorio_vacio():
    repository.seed(Reserva(
        id="R-1001",
        usuario_id="U100",
        sala="SALA-1",
        fecha="2026-09-15",
        horas=2,
        estado="ACTIVA",
    ))
    assert repository.listar_por_usuario("U100")

    repository.reset()

    assert repository.listar_por_usuario("U100") == []
    assert repository.obtener("R-1001") is None


def test_guardar_asigna_id_secuencial_desde_1001():
    r1 = repository.guardar("U100", "SALA-1", "2026-09-15", 2)
    r2 = repository.guardar("U100", "SALA-2", "2026-09-16", 3)

    assert r1.id == "R-1001"
    assert r2.id == "R-1002"
    assert r1.estado == "ACTIVA"


def test_guardar_respeta_el_maximo_existente():
    repository.seed(Reserva(
        id="R-1001",
        usuario_id="U100",
        sala="SALA-1",
        fecha="2026-09-15",
        horas=2,
        estado="ACTIVA",
    ))

    creada = repository.guardar("U200", "SALA-3", "2026-09-17", 4)

    assert creada.id == "R-1002"


def test_listar_por_usuario_solo_del_usuario():
    repository.guardar("U100", "SALA-1", "2026-09-15", 2)
    repository.guardar("U200", "SALA-2", "2026-09-16", 1)

    de_u100 = repository.listar_por_usuario("U100")

    assert len(de_u100) == 1
    assert de_u100[0].usuario_id == "U100"
    assert de_u100[0].id == "R-1001"


def test_obtener_devuelve_none_para_reserva_inexistente():
    assert repository.obtener("R-9999") is None