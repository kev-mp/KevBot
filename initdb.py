import sqlite3

conn = sqlite3.connect("discord_database.db")

c = conn.cursor()

#initialize guild table
c.execute("DROP TABLE IF EXISTS guilds")
c.execute("""CREATE TABLE IF NOT EXISTS guilds (
            guild_id TEXT PRIMARY KEY,
            timeout_percent REAL DEFAULT 0 NOT NULL
            )""")
conn.commit()

#initialize blacklist table
c.execute("DROP TABLE IF EXISTS blacklists")
c.execute("""CREATE TABLE IF NOT EXISTS blacklists (
            guild_id TEXT,
            phrase TEXT,
            PRIMARY KEY (guild_id, phrase),
            FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
            )""")

conn.commit()
conn.close()