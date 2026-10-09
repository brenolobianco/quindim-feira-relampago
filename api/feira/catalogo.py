from flask import Blueprint
from pymongo import UpdateOne
from pymongo.database import Database

from feira.banco import banco
from feira.modelos import Livro

SEED = {
    "QND-001": {"titulo": "O Jardim de Dentro", "preco_centavos": 3990, "estoque": 10},
    "QND-002": {"titulo": "Bicho-Palavra", "preco_centavos": 2990, "estoque": 10},
    "QND-003": {"titulo": "A Casa que Anda", "preco_centavos": 1995, "estoque": 10},
    "QND-004": {"titulo": "Kit Primeira Leitura", "preco_centavos": 8990, "estoque": 3},
    "QND-005": {
        "titulo": "A Lua no Bolso — edição numerada",
        "preco_centavos": 12900,
        "estoque": 1,
    },
}

rotas = Blueprint("catalogo", __name__)


def aplicar_seed(db: Database) -> None:
    db.livros.bulk_write(
        [
            UpdateOne(
                {"_id": sku},
                {"$setOnInsert": {**livro, "disponivel": livro["estoque"]}},
                upsert=True,
            )
            for sku, livro in SEED.items()
        ]
    )


@rotas.get("/v1/livros")
def listar_livros():
    livros = banco().livros.find().sort("_id")
    return {"livros": [Livro.model_validate(livro).model_dump() for livro in livros]}
