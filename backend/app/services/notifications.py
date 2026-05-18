import uuid
from typing import Any, Iterable

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.services.ws_manager import ws_manager


async def notify(
    db: AsyncSession,
    user_ids: Iterable[uuid.UUID],
    notif_type: str,
    payload: dict[str, Any],
) -> None:
    unique_ids = list({uid for uid in user_ids if uid is not None})
    if not unique_ids:
        return

    records = [Notification(user_id=uid, type=notif_type, payload=payload) for uid in unique_ids]
    db.add_all(records)
    await db.flush()

    for record in records:
        await ws_manager.send_to_user(
            record.user_id,
            {
                "id": str(record.id),
                "type": record.type,
                "payload": record.payload,
                "read": False,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            },
        )


async def list_notifications(db: AsyncSession, user_id: uuid.UUID) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.read.asc(), Notification.created_at.desc())
    )
    return list(result.scalars().all())


async def mark_read(
    db: AsyncSession,
    user_id: uuid.UUID,
    ids: list[uuid.UUID] | None,
    mark_all: bool,
) -> int:
    if not mark_all and not ids:
        return 0
    stmt = update(Notification).where(
        Notification.user_id == user_id, Notification.read.is_(False)
    )
    if not mark_all and ids:
        stmt = stmt.where(Notification.id.in_(ids))
    stmt = stmt.values(read=True)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount or 0
