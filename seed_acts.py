import asyncio
import aiosqlite
import argon2
from uuid import uuid4

_SEED_USERS = [
    ("wafflelord2",   "wafflelord2@pompey.com",   "password123"),
    ("syrup_queen2",  "syrupqueen2@pompey.com",   "password123"),
    ("gridmaster2",   "gridmaster2@pompey.com",   "password123"),
]

_SEED_ACTS = [
    # (username,      location,                                    category,       item,                               completed, claimedByUsername)
    ("wafflelord",  {"lat": "50.8013", "lng": "-1.1106"},         "Food",         "Share a waffle with a stranger",   False,  None),           # Historic Dockyard
    ("wafflelord",  {"lat": "50.8477", "lng": "-1.0645"},         "Community",    "Pick up litter for 10 minutes",    True,   "syrup_queen"),   # Cosham
    ("wafflelord",  {"lat": "50.8337", "lng": "-1.0725"},         "Sport",        "Teach someone to juggle",          False,  "gridmaster"),    # Hilsea
    ("syrup_queen", {"lat": "50.8156", "lng": "-1.0756"},         "Food",         "Buy a coffee for the next person", True,   "gridmaster"),    # North End
    ("syrup_queen", {"lat": "50.7793", "lng": "-1.0849"},         "Arts",         "Chalk a nice message on the path", False,  None),            # Southsea Castle
    ("syrup_queen", {"lat": "50.8087", "lng": "-1.0806"},         "Community",    "Water the public flower beds",     False,  "wafflelord"),    # Buckland
    ("gridmaster",  {"lat": "50.8145", "lng": "-1.0589"},         "Food",         "Hand out free waffle samples",     True,   "wafflelord"),    # Copnor
    ("gridmaster",  {"lat": "50.8410", "lng": "-1.0456"},         "Fun",          "Give someone a go on your token",  False,  None),            # Drayton
    ("gridmaster",  {"lat": "50.8456", "lng": "-1.0312"},         "Education",    "Read to a kid for 15 minutes",     False,  "syrup_queen"),   # Farlington
    ("wafflelord",  {"lat": "50.7955", "lng": "-1.1016"},         "Environment",  "Build a bird feeder from scrap",   False,  None),            # Portsmouth Cathedral
]

async def seed():
    ph = argon2.PasswordHasher()

    async with aiosqlite.connect('database.db') as db:
        user_ids = {}
        for username, email, password in _SEED_USERS:
            cursor = await db.execute("SELECT id FROM users WHERE username = ?", (username,))
            row = await cursor.fetchone()
            if row:
                user_ids[username] = row[0]
                print(f"  user already exists: {username}")
                continue

            cursor = await db.execute(
                "INSERT INTO users (uuid, username, email, passwordHash, waffle) VALUES (?, ?, ?, ?, ?)",
                (str(uuid4()), username, email, ph.hash(password), 50)
            )
            user_ids[username] = cursor.lastrowid
            print(f"  created user: {username}")

        for owner, location, category, item, completed, claimed_by_name in _SEED_ACTS:
            claimed_by_id = user_ids.get(claimed_by_name) if claimed_by_name else None
            await db.execute(
                "INSERT INTO Acts (userId, location, category, item, completed, claimedBy) VALUES (?, ?, ?, ?, ?, ?)",
                (user_ids[owner], location, category, item, completed, claimed_by_id)
            )

        await db.commit()
        print(f"  inserted {len(_SEED_ACTS)} acts")

if __name__ == '__main__':
    asyncio.run(seed())
