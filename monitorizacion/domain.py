"""Modelo de dominio del microservicio de monitorización."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4


class EstadoSesion(StrEnum):
    ACTIVA = "activa"
    CERRADA = "cerrada"


@dataclass(frozen=True)
class LecturaMetrica:
    valor: float
    unidad_medida: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def es_valida(self) -> bool:
        return self.valor == self.valor and self.unidad_medida.strip() != ""


@dataclass(frozen=True)
class UmbralSeguridad:
    valor_minimo: float
    valor_maximo: float
    tipo_metrica: str
    unidad_medida: str

    def esta_fuera_de_rango(self, valor: float) -> bool:
        return valor < self.valor_minimo or valor > self.valor_maximo


@dataclass(frozen=True)
class AnomaliaDetectadaEvent:
    event_id: UUID
    residente_id: UUID
    dispositivo_id: UUID
    metrica: str
    valor_registrado: float
    unidad_medida: str
    severidad: str
    ocurrido_en: datetime


@dataclass
class SesionMonitoreo:
    residente_id: UUID
    dispositivo_id: UUID
    session_id: UUID = field(default_factory=uuid4)
    estado: EstadoSesion = EstadoSesion.ACTIVA
    fecha_inicio: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    fecha_fin: datetime | None = None
    lecturas: list[LecturaMetrica] = field(default_factory=list)

    def registrar_lectura(self, lectura: LecturaMetrica) -> None:
        if self.estado != EstadoSesion.ACTIVA:
            raise ValueError("La sesión está cerrada")
        if not lectura.es_valida():
            raise ValueError("La lectura no es válida")
        self.lecturas.append(lectura)

    def cerrar(self) -> None:
        if self.estado == EstadoSesion.CERRADA:
            return
        self.estado = EstadoSesion.CERRADA
        self.fecha_fin = datetime.now(timezone.utc)


def determinar_severidad(lectura: LecturaMetrica, umbral: UmbralSeguridad) -> str | None:
    if lectura.unidad_medida != umbral.unidad_medida:
        raise ValueError(f"Unidad inválida para {umbral.tipo_metrica}: se esperaba {umbral.unidad_medida}")
    if not umbral.esta_fuera_de_rango(lectura.valor):
        return None
    margen = umbral.valor_maximo - umbral.valor_minimo
    distancia = umbral.valor_minimo - lectura.valor if lectura.valor < umbral.valor_minimo else lectura.valor - umbral.valor_maximo
    return "critica" if margen <= 0 or distancia >= margen * 0.25 else "advertencia"


def crear_evento(sesion: SesionMonitoreo, metrica: str, lectura: LecturaMetrica, severidad: str) -> AnomaliaDetectadaEvent:
    return AnomaliaDetectadaEvent(uuid4(), sesion.residente_id, sesion.dispositivo_id, metrica, lectura.valor, lectura.unidad_medida, severidad, lectura.timestamp)
