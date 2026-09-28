import pytest

from app.compile.loader import load_world_model
from app.compile.validate import validate_world_model
from app.engine.sessions import store


@pytest.fixture(scope="session")
def model():
    loaded = load_world_model()
    validate_world_model(loaded)
    return loaded


@pytest.fixture(autouse=True)
def reset_worlds():
    for session in store.worlds.values():
        session.reset()
    yield
    for session in store.worlds.values():
        session.reset()
