from mautrix.util.async_db import Connection, Scheme, UpgradeTable

upgrade_table = UpgradeTable()


@upgrade_table.register(description="Initial schema with OAuth support", upgrades_to=1)
async def upgrade_v1(conn: Connection, scheme: Scheme) -> None:
    # Drop old tables if they exist (cleanup from failed migrations)
    for table in (
        "webhook_old",
        "client_old",
        "matrix_message_old",
        "needs_post_migration",
    ):
        if await conn.table_exists(table):
            await conn.execute(f"DROP TABLE IF EXISTS {table}")

    # Create tables
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS client (
            user_id TEXT NOT NULL,
            token   TEXT NOT NULL,
            refresh_token TEXT,
            expiry REAL,
            PRIMARY KEY (user_id)
        )"""
    )
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS webhook (
            id        TEXT NOT NULL,
            repo      TEXT NOT NULL,
            user_id   TEXT NOT NULL,
            room_id   TEXT NOT NULL,
            secret    TEXT NOT NULL,
            github_id INTEGER,
            PRIMARY KEY (id),
            CONSTRAINT webhook_repo_room_unique UNIQUE (repo, room_id)
        )"""
    )
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS matrix_message (
            message_id TEXT NOT NULL,
            room_id    TEXT NOT NULL,
            event_id   TEXT NOT NULL,
            PRIMARY KEY (message_id, room_id)
        )"""
    )
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS avatar (
            url TEXT NOT NULL,
            mxc TEXT NOT NULL,
            PRIMARY KEY (url)
        )"""
    )
