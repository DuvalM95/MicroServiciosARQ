"""Puertos y casos de uso de monitorización."""

from typing import Protocol
from uuid import UUID

from ..dominio.modelos import AnomaliaDetectadaEvent, EvaluadorDeRiesgoService, LecturaMetrica, SesionMonitoreo, UmbralSeguridad
from .eventos import AnomaliaDetectadaIntegrationEvent


class SesionRepositoryPort(Protocol):
    def guardar(self, sesion: SesionMonitoreo) -> None: ...
    def obtener(self, session_id: UUID) -> SesionMonitoreo | None: ...


class EventPublisherPort(Protocol):
    async def publicar(self, evento: AnomaliaDetectadaIntegrationEvent) -> None: ...


class SensorInputPort(Protocol):
    def leer(self, metrica: str, unidad_medida: str) -> LecturaMetrica: ...


class ProcesarLecturaSensorUseCase:
    def __init__(self, repository: SesionRepositoryPort, publisher: EventPublisherPort, umbrales: dict[str, UmbralSeguridad], evaluador: EvaluadorDeRiesgoService):
        self.repository = repository
        self.publisher = publisher
        self.umbrales = umbrales
        self.evaluador = evaluador

    async def ejecutar(self, session_id: UUID, metrica: str, lectura: LecturaMetrica) -> tuple[SesionMonitoreo, AnomaliaDetectadaEvent | None]:
        sesion = self.repository.obtener(session_id)
        if sesion is None:
            raise LookupError("Sesión no encontrada")
        umbral = self.umbrales.get(metrica)
        if umbral is None:
            raise LookupError("Métrica sin umbral configurado")
        sesion.registrar_lectura(lectura)
        evento = sesion.evaluar_riesgo(metrica, lectura, umbral, self.evaluador)
        self.repository.guardar(sesion)
        if evento:
            await self.publisher.publicar(AnomaliaDetectadaIntegrationEvent.desde_evento_dominio(evento))
        return sesion, evento


class SimularLecturaSensorUseCase:
    def __init__(self, sensor: SensorInputPort, procesador: ProcesarLecturaSensorUseCase, umbrales: dict[str, UmbralSeguridad]):
        self.sensor = sensor
        self.procesador = procesador
        self.umbrales = umbrales

    async def ejecutar(self, session_id: UUID, metrica: str) -> tuple[SesionMonitoreo, LecturaMetrica, AnomaliaDetectadaEvent | None]:
        umbral = self.umbrales.get(metrica)
        if umbral is None:
            raise LookupError("Métrica sin umbral configurado")
        lectura = self.sensor.leer(metrica, umbral.unidad_medida)
        sesion, evento = await self.procesador.ejecutar(session_id, metrica, lectura)
        return sesion, lectura, evento


class MonitorizacionService:
    """Fachada de casos de uso consumida por la API HTTP."""

    def __init__(self, repository: SesionRepositoryPort, publisher: EventPublisherPort, sensor: SensorInputPort, umbrales: dict[str, UmbralSeguridad], evaluador: EvaluadorDeRiesgoService | None = None):
        self.repository = repository
        self.umbrales = umbrales
        self.procesar_lectura = ProcesarLecturaSensorUseCase(repository, publisher, umbrales, evaluador or EvaluadorDeRiesgoService())
        self.simular_lectura = SimularLecturaSensorUseCase(sensor, self.procesar_lectura, umbrales)

    def iniciar_sesion(self, residente_id: UUID, dispositivo_id: UUID) -> SesionMonitoreo:
        sesion = SesionMonitoreo(residente_id=residente_id, dispositivo_id=dispositivo_id)
        self.repository.guardar(sesion)
        return sesion

    async def registrar_lectura(self, session_id: UUID, metrica: str, lectura: LecturaMetrica) -> tuple[SesionMonitoreo, AnomaliaDetectadaEvent | None]:
        return await self.procesar_lectura.ejecutar(session_id, metrica, lectura)

    async def simular(self, session_id: UUID, metrica: str):
        return await self.simular_lectura.ejecutar(session_id, metrica)

    def cerrar_sesion(self, session_id: UUID) -> SesionMonitoreo:
        sesion = self.repository.obtener(session_id)
        if sesion is None:
            raise LookupError("Sesión no encontrada")
        sesion.cerrar()
        self.repository.guardar(sesion)
        return sesion
