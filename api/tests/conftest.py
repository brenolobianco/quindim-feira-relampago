import pytest

from feira.app import create_app

BANCO_DE_TESTE = "feira_teste"


@pytest.fixture
def app():
    app = create_app(MONGO_BANCO=BANCO_DE_TESTE)
    app.extensions["banco"].client.drop_database(BANCO_DE_TESTE)
    return app


@pytest.fixture
def cliente(app):
    return app.test_client()
