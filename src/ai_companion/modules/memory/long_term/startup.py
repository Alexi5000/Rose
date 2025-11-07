"""Startup initialization for the long-term memory system.

This module provides functions to initialize and verify the Qdrant vector
database collection during application startup. This ensures the memory
system is ready before the application accepts user requests.

Following the "fail fast" principle, we check dependencies at startup
rather than discovering issues during runtime when users are affected.

Usage:
    from ai_companion.modules.memory.long_term.startup import initialize_memory_system

    # In your main app startup code:
    if not initialize_memory_system():
        logger.warning("Memory system unavailable - app will run in degraded mode")
"""

import logging
from typing import Optional

from ai_companion.modules.memory.long_term.constants import QDRANT_COLLECTION_NAME
from ai_companion.modules.memory.long_term.vector_store import get_vector_store

logger = logging.getLogger(__name__)


def initialize_memory_system(required: bool = False) -> bool:
    """Initialize the long-term memory system on application startup.

    This function:
    1. Creates VectorStore singleton instance
    2. Verifies Qdrant connectivity
    3. Creates collection if it doesn't exist
    4. Validates collection is ready for use

    Args:
        required: If True, raises exception on failure. If False (default),
                 logs warning and returns False, allowing app to continue
                 in degraded mode without memory features.

    Returns:
        bool: True if memory system is ready, False if unavailable

    Raises:
        RuntimeError: Only if required=True and initialization fails

    Example:
        >>> # Graceful degradation (recommended)
        >>> if initialize_memory_system(required=False):
        ...     print("Memory features enabled")
        ... else:
        ...     print("Running without memory features")

        >>> # Fail-fast mode (for apps that require memory)
        >>> initialize_memory_system(required=True)  # Raises if fails
    """
    try:
        logger.info("🚀 Initializing long-term memory system...")

        # Get or create VectorStore singleton
        vector_store = get_vector_store()
        logger.info("✅ VectorStore instance created")

        # Initialize collection (creates if doesn't exist)
        success = vector_store.initialize_collection()

        if success:
            # Get and log collection stats
            info = vector_store.get_collection_info()
            if info:
                logger.info(
                    f"✅ Memory system ready: {info['points_count']} memories in "
                    f"'{QDRANT_COLLECTION_NAME}' (status: {info['status']})"
                )
            else:
                logger.info(f"✅ Memory system ready: '{QDRANT_COLLECTION_NAME}' collection created")
            return True
        else:
            error_msg = f"❌ Failed to initialize collection '{QDRANT_COLLECTION_NAME}'"
            logger.error(error_msg)
            if required:
                raise RuntimeError(error_msg)
            return False

    except Exception as e:
        error_msg = f"❌ Memory system initialization failed: {e}"
        logger.error(error_msg, exc_info=True)
        if required:
            raise RuntimeError(error_msg) from e
        return False


def verify_memory_system() -> Optional[dict]:
    """Verify the memory system is operational and return status.

    This is a lightweight health check that can be called periodically
    or exposed as a health endpoint.

    Returns:
        dict: Status information if available, None if system is down

        Example response:
        {
            "status": "operational",
            "collection": "long_term_memory",
            "memory_count": 42,
            "collection_status": "green"
        }

    Example:
        >>> status = verify_memory_system()
        >>> if status and status['status'] == 'operational':
        ...     print(f"Memory system OK: {status['memory_count']} memories")
        ... else:
        ...     print("Memory system unavailable")
    """
    try:
        vector_store = get_vector_store()
        info = vector_store.get_collection_info()

        if info:
            return {
                "status": "operational",
                "collection": info["name"],
                "memory_count": info["points_count"],
                "collection_status": info["status"],
            }
        else:
            logger.warning("⚠️ Memory system check: Collection not available")
            return {
                "status": "degraded",
                "collection": QDRANT_COLLECTION_NAME,
                "memory_count": 0,
                "collection_status": "unavailable",
            }

    except Exception as e:
        logger.error(f"❌ Memory system check failed: {e}")
        return None
