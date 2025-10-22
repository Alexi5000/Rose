"""Checkpointer factory for database abstraction.

This module provides a factory function to create the appropriate checkpointer
based on the configured database type (SQLite or PostgreSQL). This enables
horizontal scaling by switching from SQLite to PostgreSQL without code changes.

Example:
    >>> from ai_companion.core.checkpointer import get_checkpointer
    >>> checkpointer = get_checkpointer()
    >>> graph = graph_builder.compile(checkpointer=checkpointer)
"""

import logging
from typing import Any

from ai_companion.settings import settings

logger = logging.getLogger(__name__)


def get_checkpointer() -> Any:
    """Get the appropriate checkpointer based on configuration.

    Returns the correct checkpointer implementation (SQLite or PostgreSQL)
    based on the FEATURE_DATABASE_TYPE setting. This allows seamless switching
    between database backends for horizontal scaling.

    Returns:
        Checkpointer instance (SqliteSaver or PostgresSaver)

    Raises:
        ValueError: If database type is not supported or required config is missing
        ImportError: If required database driver is not installed

    Example:
        >>> # Using SQLite (default)
        >>> checkpointer = get_checkpointer()
        >>> type(checkpointer).__name__
        'SqliteSaver'

        >>> # Using PostgreSQL (set FEATURE_DATABASE_TYPE=postgresql)
        >>> checkpointer = get_checkpointer()
        >>> type(checkpointer).__name__
        'PostgresSaver'
    """
    database_type = settings.FEATURE_DATABASE_TYPE.lower()

    if database_type == "sqlite":
        logger.info("Using SQLite checkpointer", extra={"db_path": settings.SHORT_TERM_MEMORY_DB_PATH})
        from langgraph.checkpoint.sqlite import SqliteSaver

        return SqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH)

    elif database_type == "postgresql":
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL is required when FEATURE_DATABASE_TYPE is 'postgresql'")

        logger.info(
            "Using PostgreSQL checkpointer",
            extra={
                "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "***",
                "pool_size": settings.DATABASE_POOL_SIZE,
                "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            },
        )

        try:
            from langgraph.checkpoint.postgres import PostgresSaver
        except ImportError as e:
            raise ImportError(
                "PostgreSQL support requires 'langgraph[postgres]' and 'psycopg[binary]'. "
                "Install with: uv pip install 'langgraph[postgres]' 'psycopg[binary]'"
            ) from e

        return PostgresSaver.from_conn_string(settings.DATABASE_URL)

    else:
        raise ValueError(f"Unsupported database type: {database_type}. Must be 'sqlite' or 'postgresql'")


async def get_async_checkpointer() -> Any:
    """Get the appropriate async checkpointer based on configuration.

    Returns the correct async checkpointer implementation (AsyncSqliteSaver or
    AsyncPostgresSaver) based on the FEATURE_DATABASE_TYPE setting.

    Returns:
        Async checkpointer instance

    Raises:
        ValueError: If database type is not supported or required config is missing
        ImportError: If required database driver is not installed

    Example:
        >>> async with get_async_checkpointer() as checkpointer:
        ...     graph = graph_builder.compile(checkpointer=checkpointer)
        ...     result = await graph.ainvoke(...)
    """
    database_type = settings.FEATURE_DATABASE_TYPE.lower()

    if database_type == "sqlite":
        logger.info("Using AsyncSqlite checkpointer", extra={"db_path": settings.SHORT_TERM_MEMORY_DB_PATH})
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        return AsyncSqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH)

    elif database_type == "postgresql":
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL is required when FEATURE_DATABASE_TYPE is 'postgresql'")

        logger.info(
            "Using AsyncPostgreSQL checkpointer",
            extra={
                "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "***",
                "pool_size": settings.DATABASE_POOL_SIZE,
                "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            },
        )

        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        except ImportError as e:
            raise ImportError(
                "PostgreSQL support requires 'langgraph[postgres]' and 'psycopg[binary]'. "
                "Install with: uv pip install 'langgraph[postgres]' 'psycopg[binary]'"
            ) from e

        return AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL)

    else:
        raise ValueError(f"Unsupported database type: {database_type}. Must be 'sqlite' or 'postgresql'")


def get_database_url_for_region(region: str) -> str:
    """Get the database URL for a specific region.

    Used in multi-region deployments to route database connections to the
    appropriate regional database.

    Args:
        region: Region code ("us", "eu", "asia")

    Returns:
        Database URL for the specified region

    Raises:
        ValueError: If region is not configured or multi-region is not enabled

    Example:
        >>> url = get_database_url_for_region("eu")
        >>> checkpointer = PostgresSaver.from_conn_string(url)
    """
    if not settings.FEATURE_MULTI_REGION_ENABLED:
        raise ValueError("Multi-region is not enabled. Set FEATURE_MULTI_REGION_ENABLED=true")

    region_databases = {
        "us": settings.DATABASE_URL_US,
        "eu": settings.DATABASE_URL_EU,
        "asia": settings.DATABASE_URL_ASIA,
    }

    database_url = region_databases.get(region.lower())
    if not database_url:
        logger.warning(
            "Region database not configured, falling back to default",
            extra={"region": region, "fallback": "us"},
        )
        return settings.DATABASE_URL_US or settings.DATABASE_URL or ""

    return database_url
