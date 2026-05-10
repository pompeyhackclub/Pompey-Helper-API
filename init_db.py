import aiosqlite

_SEED_MERCH = [
    ("Waffle Iron Tee",          12, "GridLock Apparel",      "merch/waffle_iron_tee.jpg"),
    ("Crispy Corner Cap",         8, "WaffleWear Co.",        "merch/CrispyCornerCap.jpg"),
    ("Syrup Smuggler Flask",     15, "The Syrup Collective",  "merch/SyrupSmugglerFlask.jpg"),
    ("Belgian Bloc Hoodie",      25, "GridLock Apparel",      "merch/BelgianBlockHoodie.png"),
    ("Grid Life Socks",           5, "WaffleWear Co.",        "merch/GridLifeSocks.png"),
    ("Waffle Whisperer Apron",   10, "The Syrup Collective",  "merch/WaffleWhisperer.png"),
    ("Pompey Waffle Enamel Pin",  3, "Pompey Pins Ltd.",      "merch/PortsPin.jpg"),
    ("Golden Square Mug",         7, "Pompey Pins Ltd.",      "merch/golden_square_mug.jpg"),
]

async def init_db():
    async with aiosqlite.connect('database.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                passwordHash TEXT NOT NULL,
                waffle INTEGER NOT NULL DEFAULT 5
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS Acts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userId INTEGER NOT NULL,
                claimedBy INTEGER,
                location TEXT NOT NULL,
                category TEXT NOT NULL,
                item TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT FALSE,
                FOREIGN KEY (userId) REFERENCES users (id),
                FOREIGN KEY (claimedBy) REFERENCES users (id)
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS Merch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                waffles INTEGER NOT NULL,
                provider TEXT NOT NULL,
                img TEXT NOT NULL
            )
        ''')

        for name, waffles, provider, img in _SEED_MERCH:
            await db.execute(
                "INSERT OR IGNORE INTO Merch (name, waffles, provider, img) VALUES (?, ?, ?, ?)",
                (name, waffles, provider, img)
            )

        await db.commit()



if __name__ == '__main__':
    import asyncio
    asyncio.run(init_db())