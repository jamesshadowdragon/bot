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
        # -------------------------
# Giveaway Cog
# -------------------------

class Giveaways(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        # Register the persistent button
        self.bot.add_view(GiveawayView())

        # Start background task
        self.giveaway_loop.start()

    def cog_unload(self):
        self.giveaway_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Giveaway system loaded.")

    # -------------------------
    # Giveaway Loop
    # -------------------------

    @tasks.loop(seconds=30)
    async def giveaway_loop(self):
        """
        Checks every 30 seconds for giveaways that have ended.
        Winner selection will be added in Part 5.3.
        """

        giveaways = await database.get_active_giveaways()

        now = int(time.time())

        for giveaway in giveaways:

            message_id = giveaway[0]
            channel_id = giveaway[1]
            prize = giveaway[2]
            winners = giveaway[3]
            end_time = giveaway[4]

            if now >= end_time:

                print(
                    f"Giveaway ended: {message_id} ({prize})"
                )

                # Placeholder
                # Winner selection will be implemented later.

                await database.end_giveaway(message_id)

    @giveaway_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
