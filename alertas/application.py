"""Casos de uso y puertos del servicio de alertas."""

from typing import Protocol
from uuid import UUID

from .domain import Alerta


class AlertaRepositoryPort(Protocol):
    def guardar_si_nueva(self, alerta: Alerta) -> None: ...
    def listar(self) -> list[Alerta]: ...


class AlertasService:
    def __init__(self, repository: AlertaRepositoryPort):
        self.repository = repository

    def recibir(self, alerta: Alerta) -> UUID:
        self.repository.guardar_si_nueva(alerta)
        return alerta.event_id

    def listar(self) -> list[Alerta]:
        return self.repository.listar()
