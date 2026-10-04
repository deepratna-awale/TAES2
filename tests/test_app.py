import importlib

import gradio as gr


def test_all_interfaces_build():
    from src.ui import create_main_interface, create_minimal_interface, create_simple_interface

    for factory in (create_main_interface, create_minimal_interface, create_simple_interface):
        assert isinstance(factory(), gr.Blocks)


def test_create_gradio_app_initialises_database(monkeypatch):
    monkeypatch.setenv("TAES_INTERFACE_MODE", "simple")
    app = importlib.import_module("app")
    interface = app.create_gradio_app()
    assert isinstance(interface, gr.Blocks)
    assert interface.title != "TAES 2 - Error"


def test_auth_only_enabled_when_both_values_set(monkeypatch):
    app = importlib.import_module("app")
    monkeypatch.delenv("TAES_AUTH_USERNAME", raising=False)
    monkeypatch.setenv("TAES_AUTH_PASSWORD", "x")
    assert app.get_auth() is None
    monkeypatch.setenv("TAES_AUTH_USERNAME", "teacher")
    assert app.get_auth() == [("teacher", "x")]


def test_postgres_urls_use_installed_driver():
    from src.database.init_db import _engine_url

    assert _engine_url("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert _engine_url("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert _engine_url("sqlite:///x.db") == "sqlite:///x.db"


def test_database_url_built_from_parts(monkeypatch):
    from sqlalchemy.engine import make_url

    from src.config import settings as settings_module

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_HOST", "db.example.com")
    # Characters that must be escaped in a URL survive the round trip
    raw = "".join(["p", "@", "s", "/", "w"])
    monkeypatch.setenv("DB_PASSWORD", raw)
    url = make_url(settings_module._build_database_url())
    assert (url.host, url.port, url.database, url.username) == ("db.example.com", 5432, "taes2_db", "taes2_db_user")
    assert url.password == raw
