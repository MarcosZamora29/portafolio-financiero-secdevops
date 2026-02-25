import pytest
import sys
import os

# Añade la raíz del proyecto al path para importar app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app as flask_app


@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test_secret_key",
    })
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
