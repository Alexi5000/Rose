"""Administrative endpoints for system monitoring and maintenance."""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_companion.core.logging_config import get_logger
from ai_companion.modules.memory.long_term.guard import guard as memory_guard
from ai_companion.modules.memory.long_term.vector_store import get_vector_store
from ai_companion.modules.memory.long_term.constants import (
    QDRANT_COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    ENABLE_SESSION_ISOLATION,
    DEFAULT_SESSION_ID,
)

logger = get_logger(__name__)

router = APIRouter()


class MemorySystemStatus(BaseModel):
    """Memory system status response model."""

    status: str  # "healthy", "degraded", "unavailable"
    collection_name: str
    collection_exists: bool
    points_count: Optional[int] = None
    vectors_count: Optional[int] = None
    collection_status: Optional[str] = None
    embedding_model: str
    session_isolation_enabled: bool
    default_session_id: str
    guard_status: Dict[str, Any]
    last_check: str
    issues: list[str]


class GuardStatus(BaseModel):
    """Circuit breaker guard status response model."""

    is_disabled: bool
    error_count: int
    last_error_time: Optional[str]
    disable_until: Optional[str]
    window_seconds: int
    threshold: int
    cooldown_seconds: int


@router.get("/admin/memory/status", response_model=MemorySystemStatus)
async def get_memory_status() -> MemorySystemStatus:
    """Get comprehensive memory system status.

    Returns detailed information about:
    - Qdrant collection health and statistics
    - Circuit breaker / guard status
    - Configuration settings
    - Any detected issues

    This endpoint is useful for:
    - Monitoring dashboards
    - Health checks
    - Debugging memory system issues
    - Capacity planning

    Returns:
        MemorySystemStatus: Detailed status information
    """
    logger.info("admin_memory_status_requested")

    issues: list[str] = []
    status = "healthy"

    try:
        # Get vector store instance
        vector_store = get_vector_store()

        # Check collection existence and get info
        collection_info = vector_store.get_collection_info()

        if collection_info is None:
            status = "unavailable"
            issues.append("Qdrant collection does not exist or is unreachable")
            collection_exists = False
            points_count = None
            vectors_count = None
            collection_status_str = "unavailable"
        else:
            collection_exists = True
            points_count = collection_info.get("points_count", 0)
            vectors_count = collection_info.get("vectors_count", 0)
            collection_status_str = collection_info.get("status", "unknown")

            # Check for issues
            if collection_status_str != "green":
                status = "degraded"
                issues.append(f"Collection status is {collection_status_str} (expected: green)")

            if points_count == 0:
                issues.append("Collection is empty (no memories stored yet)")

            if points_count != vectors_count:
                status = "degraded"
                issues.append(f"Points count ({points_count}) != vectors count ({vectors_count})")

        # Get guard status
        import time
        from datetime import datetime

        current_time = time.time()
        recent_errors = [ts for ts in memory_guard.errors if current_time - ts <= memory_guard.window_seconds]

        guard_info = {
            "is_disabled": memory_guard.is_disabled(),
            "error_count": len(recent_errors),
            "last_error_time": datetime.fromtimestamp(recent_errors[-1]).isoformat() if recent_errors else None,
            "disable_until": datetime.fromtimestamp(memory_guard.disabled_until).isoformat() if memory_guard.disabled_until > current_time else None,
            "window_seconds": memory_guard.window_seconds,
            "threshold": memory_guard.threshold,
            "cooldown_seconds": memory_guard.cooldown_seconds,
        }

        # Check guard status
        if memory_guard.is_disabled():
            status = "degraded"
            issues.append(
                f"Memory guard is disabled due to recent errors (disabled until {guard_info['disable_until']})"
            )

        if len(recent_errors) > 0:
            issues.append(f"Memory guard has {len(recent_errors)} recent errors")

        # Build response
        return MemorySystemStatus(
            status=status,
            collection_name=QDRANT_COLLECTION_NAME,
            collection_exists=collection_exists,
            points_count=points_count,
            vectors_count=vectors_count,
            collection_status=collection_status_str,
            embedding_model=EMBEDDING_MODEL_NAME,
            session_isolation_enabled=ENABLE_SESSION_ISOLATION,
            default_session_id=DEFAULT_SESSION_ID,
            guard_status=guard_info,
            last_check=datetime.now().isoformat(),
            issues=issues,
        )

    except Exception as e:
        logger.error("admin_memory_status_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get memory status: {type(e).__name__}: {str(e)}",
        )


@router.get("/admin/memory/guard", response_model=GuardStatus)
async def get_guard_status() -> GuardStatus:
    """Get memory guard (circuit breaker) status.

    Returns information about the circuit breaker protecting the memory system:
    - Whether it's disabled
    - Error counts and timing
    - Configuration parameters

    Returns:
        GuardStatus: Circuit breaker status
    """
    logger.info("admin_guard_status_requested")

    try:
        import time
        from datetime import datetime

        current_time = time.time()
        recent_errors = [ts for ts in memory_guard.errors if current_time - ts <= memory_guard.window_seconds]

        return GuardStatus(
            is_disabled=memory_guard.is_disabled(),
            error_count=len(recent_errors),
            last_error_time=datetime.fromtimestamp(recent_errors[-1]).isoformat() if recent_errors else None,
            disable_until=datetime.fromtimestamp(memory_guard.disabled_until).isoformat() if memory_guard.disabled_until > current_time else None,
            window_seconds=memory_guard.window_seconds,
            threshold=memory_guard.threshold,
            cooldown_seconds=memory_guard.cooldown_seconds,
        )

    except Exception as e:
        logger.error("admin_guard_status_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get guard status: {type(e).__name__}: {str(e)}",
        )


@router.post("/admin/memory/guard/reset")
async def reset_guard() -> Dict[str, str]:
    """Reset the memory guard (circuit breaker).

    Clears error counts and re-enables the memory system if it was disabled.

    **Use this when:**
    - You've fixed underlying Qdrant issues
    - You want to force retry after errors
    - Testing after maintenance

    Returns:
        dict: Confirmation message
    """
    logger.info("admin_guard_reset_requested")

    try:
        memory_guard.reset()
        logger.info("admin_guard_reset_complete")

        return {
            "status": "success",
            "message": "Memory guard has been reset",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error("admin_guard_reset_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset guard: {type(e).__name__}: {str(e)}",
        )


@router.get("/admin/memory/collection")
async def get_collection_details() -> Dict:
    """Get detailed Qdrant collection information.

    Returns raw collection metadata from Qdrant, useful for debugging.

    Returns:
        dict: Raw collection information
    """
    logger.info("admin_collection_details_requested")

    try:
        vector_store = get_vector_store()
        collection_info = vector_store.get_collection_info()

        if collection_info is None:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{QDRANT_COLLECTION_NAME}' not found or unreachable",
            )

        return {
            "collection": collection_info,
            "configuration": {
                "embedding_model": EMBEDDING_MODEL_NAME,
                "session_isolation_enabled": ENABLE_SESSION_ISOLATION,
                "default_session_id": DEFAULT_SESSION_ID,
            },
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("admin_collection_details_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get collection details: {type(e).__name__}: {str(e)}",
        )
