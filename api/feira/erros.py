from dataclasses import dataclass, field

from flask import Flask, current_app, jsonify, request
from pydantic import BaseModel, ValidationError
from werkzeug.exceptions import HTTPException

ERROS_HTTP = {
    400: ("requisicao_invalida", "Requisição inválida."),
    401: ("nao_autorizado", "Não autorizado."),
    404: ("nao_encontrado", "Recurso não encontrado."),
    405: ("metodo_nao_permitido", "Método não permitido nesta rota."),
}


@dataclass
class ErroApi(Exception):
    status: int
    codigo: str
    mensagem: str
    detalhes: dict = field(default_factory=dict)


def validar_corpo[M: BaseModel](modelo: type[M]) -> M:
    try:
        return modelo.model_validate(request.get_json(silent=True))
    except ValidationError as erro:
        campos = [
            {"campo": ".".join(str(parte) for parte in falha["loc"]), "mensagem": falha["msg"]}
            for falha in erro.errors()
        ]
        raise ErroApi(
            400, "requisicao_invalida", "Corpo fora do contrato.", {"campos": campos}
        ) from erro


def resposta_de_erro(status: int, codigo: str, mensagem: str, detalhes: dict | None = None):
    corpo = {"erro": {"codigo": codigo, "mensagem": mensagem, "detalhes": detalhes or {}}}
    return jsonify(corpo), status


def tratar_erro_api(erro: ErroApi):
    return resposta_de_erro(erro.status, erro.codigo, erro.mensagem, erro.detalhes)


def tratar_erro_http(erro: HTTPException):
    codigo, mensagem = ERROS_HTTP.get(erro.code, ("erro_http", erro.description))
    return resposta_de_erro(erro.code, codigo, mensagem)


def tratar_erro_inesperado(erro: Exception):
    current_app.logger.exception("Erro inesperado", exc_info=erro)
    return resposta_de_erro(500, "erro_interno", "Erro interno. Tente novamente.")


def registrar_tratadores(app: Flask) -> None:
    app.register_error_handler(ErroApi, tratar_erro_api)
    app.register_error_handler(HTTPException, tratar_erro_http)
    app.register_error_handler(Exception, tratar_erro_inesperado)
