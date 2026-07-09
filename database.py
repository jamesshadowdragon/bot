import aiosqlite

DB_NAME = "invites.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        # Invite counts
        await db.execute("""
        CREATE TABLE IF NOT EXISTS invites (
            user_id INTEGER PRIMARY KEY,
            invite_count INTEGER DEFAULT 0
        )
        """)

        # Who invited who
        await db.execute("""
        CREATE TABLE IF NOT EXISTS members (
            member_id INTEGER PRIMARY KEY,
            inviter_id INTEGER
        )
        """)

        # Giveaways
        await db.execute("""
        CREATE TABLE IF NOT EXISTS giveaways (
            message_id INTEGER PRIMARY KEY,
            channel_id INTEGER,
            prize TEXT,
            winners INTEGER,
            end_time INTEGER,
            ended INTEGER DEFAULT 0
        )
        """)

        # Giveaway entries
        await db.execute("""
        CREATE TABLE IF NOT EXISTS giveaway_entries (
            message_id INTEGER,
            user_id INTEGER
        )
        """)

        await db.commit()


# -----------------------------
# Invite Functions
# -----------------------------

async def get_invites(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            "SELECT invite_count FROM invites WHERE user_id=?",
            (user_id,)
        )

        row = await cursor.fetchone()

        if row:
            return row[0]

        await db.execute(
            "INSERT INTO invites(user_id, invite_count) VALUES(?,0)",
            (user_id,)
        )

        await db.commit()

        return 0


async def add_invite(user_id: int):
    invites = await get_invites(user_id)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE invites SET invite_count=? WHERE user_id=?",
            (invites + 1, user_id)
        )
        await db.commit()


async def remove_invite(user_id: int):
    invites = await get_invites(user_id)

    if invites <= 0:
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE invites SET invite_count=? WHERE user_id=?",
            (invites - 1, user_id)
        )
        await db.commit()


# -----------------------------
# Member Tracking
# -----------------------------

async def save_inviter(member_id: int, inviter_id: int):
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        INSERT OR REPLACE INTO members(member_id, inviter_id)
        VALUES(?,?)
        """, (member_id, inviter_id))

        await db.commit()


async def get_inviter(member_id: int):
    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            "SELECT inviter_id FROM members WHERE member_id=?",
            (member_id,)
        )

        row = await cursor.fetchone()

        if row:
            return row[0]

        return None
