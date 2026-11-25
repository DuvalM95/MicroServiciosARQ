"""Adaptadores de persistencia del servicio de alertas."""

from uuid import UUID

from .domain import Alerta


class InMemoryAlertaRepository:
    def __init__(self):
        self._alertas: dict[UUID, Alerta] = {}

    def guardar_si_nueva(self, alerta: Alerta) -> None:
        self._alertas.setdefault(alerta.event_id, alerta)

    def listar(self) -> list[Alerta]:
        return list(self._alertas.values())
