import os
import secrets

from fastapi import HTTPException, Request

from ai_companion.settings import settings


def require_admin(request: Request) -> None:
    token = os.environ.get("ROSE_ADMIN_TOKEN", settings.ROSE_ADMIN_TOKEN).strip()
    if len(token) < 32:
        raise HTTPException(status_code=503, detail="Administrative access is not configured")
    authorization = request.headers.get("authorization", "")
    scheme, _, supplied = authorization.partition(" ")
    if scheme.lower() != "bearer" or not secrets.compare_digest(supplied.encode(), token.encode()):
        raise HTTPException(
            status_code=401,
            detail="Administrator authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )
