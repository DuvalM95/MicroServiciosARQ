"""Contrato de integración que sale del microservicio de monitorización."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ..dominio.modelos import AnomaliaDetectadaEvent


@dataclass(frozen=True)
class AnomaliaDetectadaIntegrationEvent:
    event_id: UUID
    residente_id: UUID
    dispositivo_id: UUID
    metrica: str
    valor_registrado: float
    unidad_medida: str
    severidad: str
    ocurrido_en: datetime

    @classmethod
    def desde_evento_dominio(cls, evento: AnomaliaDetectadaEvent) -> "AnomaliaDetectadaIntegrationEvent":
        return cls(evento.event_id, evento.residente_id, evento.dispositivo_id, evento.metrica, evento.valor_registrado, evento.unidad_medida, evento.severidad, evento.ocurrido_en)
