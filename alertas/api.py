"""Microservicio receptor de anomalías e incidentes."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Microservicio de Alertas e Incidentes", version="1.0.0")
eventos: dict[UUID, dict] = {}


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
    eventos.setdefault(evento.event_id, {**evento.model_dump(mode="json"), "recibido_en": datetime.now(timezone.utc).isoformat(), "estado": "pendiente"})
    return {"accepted": True, "event_id": evento.event_id}


@app.get("/alerts")
def listar_alertas():
    return list(eventos.values())
