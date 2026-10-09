from flask import Flask, current_app
from pymongo import MongoClient
from pymongo.database import Database


def conectar(app: Flask) -> None:
    cliente = MongoClient(app.config["MONGO_URL"], tz_aware=True, serverSelectionTimeoutMS=2000)
    app.extensions["banco"] = cliente[app.config["MONGO_BANCO"]]


def banco() -> Database:
    return current_app.extensions["banco"]
