"""Adaptadores de almacenamiento, publicación HTTP y simulador."""

import os
import random
from uuid import UUID

import httpx

from .domain import AnomaliaDetectadaEvent, SesionMonitoreo


class InMemorySesionRepository:
    def __init__(self):
        self._sesiones: dict[UUID, SesionMonitoreo] = {}

    def guardar(self, sesion: SesionMonitoreo) -> None:
        self._sesiones[sesion.session_id] = sesion

    def obtener(self, session_id: UUID) -> SesionMonitoreo | None:
        return self._sesiones.get(session_id)


class HttpEventPublisher:
    def __init__(self, alerts_url: str | None = None):
        self.alerts_url = (alerts_url or os.getenv("ALERTS_SERVICE_URL", "http://localhost:8001" )).rstrip("/")

    async def publicar(self, evento: AnomaliaDetectadaEvent) -> None:
        payload = {
            "event_id": str(evento.event_id), "residente_id": str(evento.residente_id),
            "dispositivo_id": str(evento.dispositivo_id), "metrica": evento.metrica,
            "valor_registrado": evento.valor_registrado, "unidad_medida": evento.unidad_medida,
            "severidad": evento.severidad, "ocurrido_en": evento.ocurrido_en.isoformat(),
        }
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.post(f"{self.alerts_url}/events/anomalies", json=payload)
            response.raise_for_status()


class SimuladorSensores:
    @staticmethod
    def generar_lectura(metrica: str) -> float:
        rangos = {"frecuencia_cardiaca": (45, 145), "temperatura_corporal": (35.0, 40.5), "humedad": (25, 85), "temperatura_ambiente": (18, 34)}
        minimo, maximo = rangos.get(metrica, (0, 100))
        return round(random.uniform(minimo, maximo), 1)
