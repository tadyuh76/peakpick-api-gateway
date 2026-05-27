from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class EventType(StrEnum):
    CART_CREATED = "CartCreated"
    ORDER_PAID = "OrderPaid"
    PICKUP_SLOT_RESERVED = "PickupSlotReserved"
    PICKUP_SLOT_FULL = "PickupSlotFull"
    INVENTORY_RESERVED = "InventoryReserved"
    INVENTORY_SHORTAGE_DETECTED = "InventoryShortageDetected"
    ORDER_PREPARING = "OrderPreparing"
    ORDER_PLACED_IN_SLOT = "OrderPlacedInSlot"
    ORDER_READY = "OrderReady"
    ORDER_PICKED_UP = "OrderPickedUp"
    ORDER_EXPIRED = "OrderExpired"
    NOTIFICATION_REQUESTED = "NotificationRequested"
    ANALYTICS_UPDATED = "AnalyticsUpdated"


class EventEnvelope(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    aggregate_id: str
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    payload: dict[str, Any]
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def new_event(
    event_type: EventType,
    aggregate_id: str,
    source: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> EventEnvelope:
    return EventEnvelope(
        event_type=event_type,
        aggregate_id=aggregate_id,
        source=source,
        payload=payload,
        correlation_id=correlation_id or str(uuid4()),
    )
