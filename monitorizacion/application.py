"""Casos de uso y puertos de aplicación."""

from typing import Protocol
from uuid import UUID

from .domain import AnomaliaDetectadaEvent, LecturaMetrica, SesionMonitoreo, UmbralSeguridad, crear_evento, determinar_severidad


class SesionRepositoryPort(Protocol):
    def guardar(self, sesion: SesionMonitoreo) -> None: ...
    def obtener(self, session_id: UUID) -> SesionMonitoreo | None: ...


class EventPublisherPort(Protocol):
    async def publicar(self, evento: AnomaliaDetectadaEvent) -> None: ...


class MonitorizacionService:
    def __init__(self, repository: SesionRepositoryPort, publisher: EventPublisherPort, umbrales: dict[str, UmbralSeguridad]):
        self.repository = repository
        self.publisher = publisher
        self.umbrales = umbrales

    def iniciar_sesion(self, residente_id: UUID, dispositivo_id: UUID) -> SesionMonitoreo:
        sesion = SesionMonitoreo(residente_id=residente_id, dispositivo_id=dispositivo_id)
        self.repository.guardar(sesion)
        return sesion

    async def procesar_lectura(self, session_id: UUID, metrica: str, lectura: LecturaMetrica) -> tuple[SesionMonitoreo, AnomaliaDetectadaEvent | None]:
        sesion = self.repository.obtener(session_id)
        if sesion is None:
            raise LookupError("Sesión no encontrada")
        sesion.registrar_lectura(lectura)
        self.repository.guardar(sesion)
        umbral = self.umbrales.get(metrica)
        if umbral is None:
            return sesion, None
        severidad = determinar_severidad(lectura, umbral)
        if severidad is None:
            return sesion, None
        evento = crear_evento(sesion, metrica, lectura, severidad)
        await self.publisher.publicar(evento)
        return sesion, evento

    def cerrar_sesion(self, session_id: UUID) -> SesionMonitoreo:
        sesion = self.repository.obtener(session_id)
        if sesion is None:
            raise LookupError("Sesión no encontrada")
        sesion.cerrar()
        self.repository.guardar(sesion)
        return sesion
