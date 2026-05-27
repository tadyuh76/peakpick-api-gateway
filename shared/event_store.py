from __future__ import annotations

import asyncio
import json

from shared.events import EventEnvelope


class PostgresEventStore:
    def __init__(self, database_url: str):
        self.database_url = database_url

    async def append(self, event: EventEnvelope) -> None:
        await asyncio.to_thread(self._append_sync, event)

    def _append_sync(self, event: EventEnvelope) -> None:
        import psycopg

        with psycopg.connect(self.database_url) as conn:
            conn.execute(
                """
                INSERT INTO event_log (
                    event_id, event_type, aggregate_id, correlation_id,
                    source, payload, occurred_at
                )
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (event_id) DO NOTHING
                """,
                (
                    event.event_id,
                    event.event_type,
                    event.aggregate_id,
                    event.correlation_id,
                    event.source,
                    json.dumps(event.payload),
                    event.occurred_at,
                ),
            )

