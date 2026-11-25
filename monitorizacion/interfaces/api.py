"""API HTTP del microservicio de monitorización."""

from datetime import datetime
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..aplicacion.casos_uso import MonitorizacionService
from ..dominio.modelos import EvaluadorDeRiesgoService, LecturaMetrica, UmbralSeguridad
from ..infraestructura.adaptadores import EventBusPublisherAdapter, SesionRepositoryAdapter, SimuladorSensoresAdapter

app = FastAPI(title="Microservicio de Monitorización", version="1.0.0", description="Sesiones de monitorización y detección de anomalías.")
repository = SesionRepositoryAdapter()
service = MonitorizacionService(repository, EventBusPublisherAdapter(), SimuladorSensoresAdapter(), {
    "frecuencia_cardiaca": UmbralSeguridad(50, 110, "frecuencia_cardiaca", "lpm"),
    "temperatura_corporal": UmbralSeguridad(35.5, 38.0, "temperatura_corporal", "°C"),
    "humedad": UmbralSeguridad(30, 70, "humedad", "%"),
    "temperatura_ambiente": UmbralSeguridad(20, 28, "temperatura_ambiente", "°C"),
}, EvaluadorDeRiesgoService())


class IniciarSesion(BaseModel):
    residente_id: UUID
    dispositivo_id: UUID


class NuevaLectura(BaseModel):
    metrica: str = Field(min_length=1, max_length=60)
    valor: float
    unidad_medida: str = Field(min_length=1, max_length=20)
    timestamp: datetime | None = None


@app.get("/health")
def health():
    return {"status": "ok", "service": "monitorizacion"}


@app.get("/thresholds")
def thresholds():
    return {nombre: {"minimo": u.valor_minimo, "maximo": u.valor_maximo, "unidad": u.unidad_medida} for nombre, u in service.umbrales.items()}


@app.post("/sessions", status_code=201)
def iniciar_sesion(body: IniciarSesion):
    s = service.iniciar_sesion(body.residente_id, body.dispositivo_id)
    return {"session_id": s.session_id, "residente_id": s.residente_id, "dispositivo_id": s.dispositivo_id, "estado": s.estado, "fecha_inicio": s.fecha_inicio}


@app.post("/sessions/{session_id}/readings", status_code=201)
async def registrar_lectura(session_id: UUID, body: NuevaLectura):
    try:
        sesion, evento = await service.registrar_lectura(session_id, body.metrica, LecturaMetrica(body.valor, body.unidad_medida, body.timestamp or datetime.now().astimezone()))
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503, f"No se pudo entregar el evento al servicio de alertas: {exc}") from exc
    return {"session_id": sesion.session_id, "metrica": body.metrica, "valor": body.valor, "unidad_medida": body.unidad_medida, "anomalia": evento is not None, "evento_id": evento.event_id if evento else None, "severidad": evento.severidad if evento else None}


@app.post("/sessions/{session_id}/simulate", status_code=201)
async def simular_lectura(session_id: UUID, metrica: str = "frecuencia_cardiaca"):
    try:
        sesion, lectura, evento = await service.simular(session_id, metrica)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503, f"No se pudo entregar el evento al servicio de alertas: {exc}") from exc
    return {"session_id": sesion.session_id, "metrica": metrica, "valor": lectura.valor, "unidad_medida": lectura.unidad_medida, "anomalia": evento is not None, "evento_id": evento.event_id if evento else None, "severidad": evento.severidad if evento else None}


@app.post("/sessions/{session_id}/close")
def cerrar_sesion(session_id: UUID):
    try:
        s = service.cerrar_sesion(session_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"session_id": s.session_id, "estado": s.estado, "fecha_fin": s.fecha_fin}
