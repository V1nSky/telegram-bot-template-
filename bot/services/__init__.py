"""Service layer — place your business logic here.

Create one module per domain entity, e.g.::

    bot/services/
        notification.py   # push notifications to users
        payment.py        # payment processing
        analytics.py      # usage analytics

Each service module should expose a class or plain async functions
that accept a :class:`sqlalchemy.ext.asyncio.AsyncSession` and return
domain objects. Keep handlers thin — call services from handlers,
not the other way around.

Example service::

    # bot/services/notification.py
    from sqlalchemy.ext.asyncio import AsyncSession
    from bot.database.repository import UserRepository

    async def broadcast(session: AsyncSession, text: str, bot) -> int:
        repo = UserRepository(session)
        users = await repo.list_active()
        sent = 0
        for user in users:
            try:
                await bot.send_message(user.telegram_id, text)
                sent += 1
            except Exception:
                pass
        return sent
"""
