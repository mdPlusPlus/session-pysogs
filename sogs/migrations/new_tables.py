import logging
from .exc import DatabaseUpgradeRequired


# { table_name => { 'sqlite': ['query1', 'query2'], 'pgsql': "query1; query2" } }
table_creations = {
    'user_request_nonces': {
        'sqlite': [
            """
CREATE TABLE user_request_nonces (
    user INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    nonce BLOB NOT NULL UNIQUE,
    expiry FLOAT NOT NULL DEFAULT ((julianday('now') - 2440587.5 + 1.0)*86400.0) /* now + 24h */
)
""",
            """
CREATE INDEX user_request_nonces_expiry ON user_request_nonces(expiry)
""",
        ],
        'pgsql': """
CREATE TABLE user_request_nonces (
    "user" BIGINT NOT NULL REFERENCES users ON DELETE CASCADE,
    nonce BYTEA NOT NULL UNIQUE,
    expiry FLOAT NOT NULL DEFAULT (extract(epoch from now() + '24 hours'))
);
CREATE INDEX user_request_nonces_expiry ON user_request_nonces(expiry)
""",
    },
    'inbox': {
        'sqlite': [
            """
CREATE TABLE inbox (
    id INTEGER PRIMARY KEY,
    recipient INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sender INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body BLOB NOT NULL,
    posted_at FLOAT DEFAULT ((julianday('now') - 2440587.5)*86400.0),
    expiry FLOAT DEFAULT ((julianday('now') - 2440587.5 + 15.0)*86400.0) /* now + 15 days */
)
""",
            """
CREATE INDEX inbox_recipient ON inbox(recipient)
""",
        ],
        'pgsql': """
CREATE TABLE inbox (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    recipient BIGINT NOT NULL REFERENCES users ON DELETE CASCADE,
    sender BIGINT NOT NULL REFERENCES users ON DELETE CASCADE,
    body BYTEA NOT NULL,
    posted_at FLOAT DEFAULT (extract(epoch from now())),
    expiry FLOAT DEFAULT (extract(epoch from now() + '15 days'))
);
CREATE INDEX inbox_recipient ON inbox(recipient);
""",
    },
    'needs_blinding': {
        'sqlite': [
            """
CREATE TABLE needs_blinding (
    blinded_abs TEXT NOT NULL PRIMARY KEY,
    "user" BIGINT NOT NULL UNIQUE REFERENCES users ON DELETE CASCADE
)
"""
        ],
        'pgsql': """
CREATE TABLE needs_blinding (
    blinded_abs TEXT NOT NULL PRIMARY KEY,
    "user" BIGINT NOT NULL UNIQUE REFERENCES users ON DELETE CASCADE
)
""",
    },
}


def migrate(conn, *, check_only):
    """Adds new tables that don't have any special migration requirement beyond creation"""

    from .. import db

    added = False

    for table, v in table_creations.items():
        if table in db.metadata.tables:
            continue

        logging.warning(f"DB migration: Adding new table {table}")
        if check_only:
            raise DatabaseUpgradeRequired(f"new table {table}")

        if db.engine.name == 'sqlite':
            for query in v['sqlite']:
                conn.execute(query)
        else:
            conn.execute(v['pgsql'])

        added = True

    return added