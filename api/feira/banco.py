from bson import ObjectId
from flask import Flask, current_app
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from feira.erros import ErroApi


def conectar(app: Flask) -> None:
    cliente = MongoClient(app.config["MONGO_URL"], tz_aware=True, serverSelectionTimeoutMS=2000)
    app.extensions["banco"] = cliente[app.config["MONGO_BANCO"]]


def banco() -> Database:
    return current_app.extensions["banco"]


def buscar_por_id(colecao: Collection, identificador: str) -> dict:
    if ObjectId.is_valid(identificador):
        documento = colecao.find_one({"_id": ObjectId(identificador)})
        if documento is not None:
            return documento
    raise ErroApi(404, "nao_encontrado", "Recurso não encontrado.")
