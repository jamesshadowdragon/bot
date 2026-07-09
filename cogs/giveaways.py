# -----------------------------
# Giveaway Functions
# -----------------------------

async def create_giveaway(message_id, channel_id, prize, winners, end_time):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT INTO giveaways
        (message_id, channel_id, prize, winners, end_time, ended)
        VALUES (?, ?, ?, ?, ?, 0)
        """, (
            message_id,
            channel_id,
            prize,
            winners,
            end_time
        ))
        await db.commit()


async def end_giveaway(message_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE giveaways SET ended=1 WHERE message_id=?",
            (message_id,)
        )
        await db.commit()


async def get_active_giveaways():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT message_id,
               channel_id,
               prize,
               winners,
               end_time
        FROM giveaways
        WHERE ended=0
        """)

        return await cursor.fetchall()


async def add_entry(message_id, user_id):
    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT *
        FROM giveaway_entries
        WHERE message_id=?
        AND user_id=?
        """, (message_id, user_id))

        exists = await cursor.fetchone()

        if exists:
            return

        await db.execute("""
        INSERT INTO giveaway_entries
        (message_id, user_id)
        VALUES (?, ?)
        """, (
            message_id,
            user_id
        ))

        await db.commit()


async def remove_entry(message_id, user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        DELETE FROM giveaway_entries
        WHERE message_id=?
        AND user_id=?
        """, (
            message_id,
            user_id
        ))
        await db.commit()


async def get_entries(message_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT user_id
        FROM giveaway_entries
        WHERE message_id=?
        """, (message_id,))

        rows = await cursor.fetchall()

        return [row[0] for row in rows]
