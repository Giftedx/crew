"""Database dependency group definitions."""

# Core database dependencies
DATABASE_GROUP: set[str] = {
    "sqlalchemy",
    "alembic",
    "psycopg2",
    "psycopg2-binary",
    "asyncpg",
    "aiomysql",
    "pymysql",
    "aiosqlite",
}

# Optional database dependencies
DATABASE_OPTIONAL: set[str] = {
    "sqlalchemy-utils",
    "marshmallow",
    "pydantic-sqlalchemy",
    "databases",
    "tortoise-orm",
    "peewee",
    "pony",
    "sqlmodel",
}
