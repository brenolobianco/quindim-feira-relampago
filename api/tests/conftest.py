import pytest

from feira.app import create_app
from feira.catalogo import aplicar_seed

BANCO_DE_TESTE = "feira_teste"
TOKEN_DE_ADMIN = "token-de-teste"


@pytest.fixture
def app():
    app = create_app(MONGO_BANCO=BANCO_DE_TESTE, ADMIN_TOKEN=TOKEN_DE_ADMIN)
    app.extensions["banco"].client.drop_database(BANCO_DE_TESTE)
    aplicar_seed(app.extensions["banco"])
    return app


@pytest.fixture
def banco(app):
    return app.extensions["banco"]


@pytest.fixture
def cliente(app):
    return app.test_client()
