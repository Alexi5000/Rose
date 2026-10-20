from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def admin_client(monkeypatch):
    from fastapi import FastAPI

    from ai_companion.interfaces.web.routes import admin

    app = FastAPI()
    app.include_router(admin.router, prefix="/api/v1")
    effect = Mock()
    monkeypatch.setattr(admin.memory_guard, "reset", effect)
    return TestClient(app), effect


@pytest.mark.parametrize("configured", [None, "", "short"])
def test_admin_disabled_without_strong_configuration(monkeypatch, admin_client, configured):
    client, effect = admin_client
    if configured is None:
        monkeypatch.delenv("ROSE_ADMIN_TOKEN", raising=False)
    else:
        monkeypatch.setenv("ROSE_ADMIN_TOKEN", configured)
    response = client.post("/api/v1/admin/memory/guard/reset", headers={"Authorization": "Bearer short"})
    assert response.status_code == 503
    effect.assert_not_called()


@pytest.mark.parametrize("authorization", ["", "Bearer wrong", "Basic " + "x" * 32])
def test_admin_denies_invalid_credentials(monkeypatch, admin_client, authorization):
    client, effect = admin_client
    monkeypatch.setenv("ROSE_ADMIN_TOKEN", "x" * 32)
    response = client.post("/api/v1/admin/memory/guard/reset", headers={"Authorization": authorization})
    assert response.status_code == 401
    effect.assert_not_called()


def test_authorized_admin_keeps_operation(monkeypatch, admin_client):
    client, effect = admin_client
    monkeypatch.setenv("ROSE_ADMIN_TOKEN", "x" * 32)
    response = client.post("/api/v1/admin/memory/guard/reset", headers={"Authorization": "Bearer " + "x" * 32})
    assert response.status_code == 200
    effect.assert_called_once_with()


@pytest.mark.parametrize("path", ["status", "guard", "collection"])
def test_admin_read_routes_are_protected(monkeypatch, admin_client, path):
    client, _ = admin_client
    monkeypatch.setenv("ROSE_ADMIN_TOKEN", "x" * 32)
    assert client.get("/api/v1/admin/memory/" + path).status_code == 401
