"""Microservicio receptor de anomalías e incidentes."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .adapters import InMemoryAlertaRepository
from .application import AlertasService
from .domain import Alerta as AlertaDomain

app = FastAPI(title="Microservicio de Alertas e Incidentes", version="1.0.0")
service = AlertasService(InMemoryAlertaRepository())


class Anomalia(BaseModel):
    event_id: UUID
    residente_id: UUID
    dispositivo_id: UUID
    metrica: str
    valor_registrado: float
    unidad_medida: str
    severidad: str = Field(pattern="^(advertencia|critica)$")
    ocurrido_en: datetime


@app.get("/health")
def health():
    return {"status": "ok", "service": "alertas"}


@app.post("/events/anomalies", status_code=202)
def recibir_anomalia(evento: Anomalia):
    service.recibir(AlertaDomain(**evento.model_dump(), recibido_en=datetime.now(timezone.utc)))
    return {"accepted": True, "event_id": evento.event_id}


@app.get("/alerts")
def listar_alertas():
    return [{**a.__dict__, "event_id": str(a.event_id), "residente_id": str(a.residente_id), "dispositivo_id": str(a.dispositivo_id), "ocurrido_en": a.ocurrido_en.isoformat(), "recibido_en": a.recibido_en.isoformat()} for a in service.listar()]
