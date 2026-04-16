import os
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")

from src.app import create_app  # noqa: E402


@pytest.fixture()
def app():
    app = create_app("test")
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()
