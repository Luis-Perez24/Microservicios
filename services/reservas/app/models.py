from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ModeloReserva(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ReservaRequest(ModeloReserva):
    """Cuerpo de POST /reservas. `horas` se valida a mano en el router para
    poder devolver 400 (el contrato prohibe Field(gt=0), que daria 422)."""

    usuario_id: str
    sala: str
    fecha: str
    horas: int


class Reserva(ModeloReserva):
    id: str
    usuario_id: str
    sala: str
    fecha: str
    horas: int
    estado: str