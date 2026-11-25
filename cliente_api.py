"""Adaptador HTTP usado por la interfaz para consumir los microservicios."""

import os
from datetime import datetime

import httpx


class ClienteApi:
    def __init__(self, monitorizacion_url: str | None = None, alertas_url: str | None = None):
        self.monitorizacion_url = (monitorizacion_url or os.getenv("MONITORIZACION_SERVICE_URL", "http://localhost:8000")).rstrip("/")
        self.alertas_url = (alertas_url or os.getenv("ALERTS_SERVICE_URL", "http://localhost:8001")).rstrip("/")

    @staticmethod
    def _request(method: str, url: str, **kwargs):
        response = httpx.request(method, url, timeout=4, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else None

    def obtener_umbrales(self) -> dict:
        return self._request("GET", f"{self.monitorizacion_url}/thresholds")

    def iniciar_sesion(self, residente_id: str, dispositivo_id: str) -> dict:
        return self._request("POST", f"{self.monitorizacion_url}/sessions", json={"residente_id": residente_id, "dispositivo_id": dispositivo_id})

    def registrar_lectura(self, session_id: str, metrica: str, valor: float, unidad: str, timestamp: datetime) -> dict:
        return self._request("POST", f"{self.monitorizacion_url}/sessions/{session_id}/readings", json={"metrica": metrica, "valor": valor, "unidad_medida": unidad, "timestamp": timestamp.isoformat()})

    def simular_lectura(self, session_id: str, metrica: str) -> dict:
        return self._request("POST", f"{self.monitorizacion_url}/sessions/{session_id}/simulate", params={"metrica": metrica})

    def cerrar_sesion(self, session_id: str) -> dict:
        return self._request("POST", f"{self.monitorizacion_url}/sessions/{session_id}/close")

    def listar_alertas(self) -> list[dict]:
        return self._request("GET", f"{self.alertas_url}/alerts")
