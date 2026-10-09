import os

from flask import Flask
from pymongo.errors import PyMongoError

from feira import admin, catalogo
from feira.banco import banco, conectar
from feira.erros import ErroApi, registrar_tratadores


def create_app(**config) -> Flask:
    app = Flask(__name__)
    app.config.update(
        MONGO_URL=os.environ.get("MONGO_URL", "mongodb://localhost:27017"),
        MONGO_BANCO=os.environ.get("MONGO_BANCO", "feira"),
        ADMIN_TOKEN=os.environ.get("ADMIN_TOKEN", ""),
    )
    app.config.update(config)
    conectar(app)
    catalogo.aplicar_seed(app.extensions["banco"])
    registrar_tratadores(app)
    app.add_url_rule("/healthz", view_func=healthz)
    app.register_blueprint(catalogo.rotas)
    app.register_blueprint(admin.rotas)
    return app


def healthz():
    try:
        banco().command("ping")
    except PyMongoError as erro:
        raise ErroApi(
            503, "banco_indisponivel", "A API não conseguiu falar com o MongoDB."
        ) from erro
    return {"status": "ok"}
