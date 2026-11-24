"""SQLAlchemy engine, session factory, and declarative base."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base declarative class for all TriVault ORM models."""


def build_engine(
    database_url: str,
    *,
    use_null_pool: bool = False,
    pool_recycle: int = 300,
) -> Engine:
    """Create a SQLAlchemy engine compatible with MySQL, PostgreSQL, and serverless."""
    engine_kwargs: dict[str, object] = {
        "pool_pre_ping": True,
        "future": True,
    }
    if use_null_pool:
        engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs["pool_recycle"] = pool_recycle

    return create_engine(database_url, **engine_kwargs)


def create_session_factory(engine: Engine) -> sessionmaker:
    """Return a configured SQLAlchemy session factory."""
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


_settings = get_settings()
engine = build_engine(
    _settings.DATABASE_URL,
    use_null_pool=_settings.DB_USE_NULL_POOL,
    pool_recycle=_settings.DB_POOL_RECYCLE,
)
SessionLocal = create_session_factory(engine)
