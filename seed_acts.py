import asyncio
import aiosqlite
import argon2
from uuid import uuid4

_SEED_USERS = [
    ("wafflelord",   "wafflelord@pompey.com",   "password123"),
    ("syrup_queen",  "syrupqueen@pompey.com",   "password123"),
    ("gridmaster",   "gridmaster@pompey.com",   "password123"),
]

_SEED_ACTS = [
    # (username,      location,              category,       item,                          completed, claimedByUsername)
    ("wafflelord",  "Albert Road",         "Food",         "Share a waffle with a stranger",   False,  None),
    ("wafflelord",  "Southsea Common",     "Community",    "Pick up litter for 10 minutes",    True,   "syrup_queen"),
    ("wafflelord",  "Fratton Park",        "Sport",        "Teach someone to juggle",          False,  "gridmaster"),
    ("syrup_queen", "Gunwharf Quays",      "Food",         "Buy a coffee for the next person",  True,   "gridmaster"),
    ("syrup_queen", "Old Portsmouth",      "Arts",         "Chalk a nice message on the path", False,  None),
    ("syrup_queen", "Victoria Park",       "Community",    "Water the public flower beds",     False,  "wafflelord"),
    ("gridmaster",  "Palmerston Road",     "Food",         "Hand out free waffle samples",     True,   "wafflelord"),
    ("gridmaster",  "Clarence Pier",       "Fun",          "Give someone a go on your token",  False,  None),
    ("gridmaster",  "Portsmouth Library",  "Education",    "Read to a kid for 15 minutes",     False,  "syrup_queen"),
    ("wafflelord",  "Eastney Beach",       "Environment",  "Build a bird feeder from scrap",   False,  None),
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
