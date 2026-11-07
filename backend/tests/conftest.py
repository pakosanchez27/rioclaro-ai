"""Aislar toda la suite de la base y la cuota usadas por la aplicación."""

import pytest


@pytest.fixture(autouse=True)
def isolated_default_database(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "default_test.db"))
    monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "Development")
    monkeypatch.delenv("WEBSITE_INSTANCE_ID", raising=False)
