"""Entidades del dominio de alertas."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Alerta:
    event_id: UUID
    residente_id: UUID
    dispositivo_id: UUID
    metrica: str
    valor_registrado: float
    unidad_medida: str
    severidad: str
    ocurrido_en: datetime
    recibido_en: datetime
    estado: str = "pendiente"
