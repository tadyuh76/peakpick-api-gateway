from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    service_name: str
    event_bus: str
    rabbitmq_url: str
    event_exchange: str
    database_url: str


def get_settings(default_service_name: str) -> Settings:
    return Settings(
        service_name=os.getenv("SERVICE_NAME", default_service_name),
        event_bus=os.getenv("EVENT_BUS", "memory"),
        rabbitmq_url=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"),
        event_exchange=os.getenv("EVENT_EXCHANGE", "peakpick.events"),
        database_url=os.getenv("DATABASE_URL", ""),
    )

