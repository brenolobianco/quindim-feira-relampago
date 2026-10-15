import hashlib
import hmac
from typing import Literal

from bson import ObjectId
from flask import Blueprint, current_app, request
from pydantic import AwareDatetime, BaseModel, Field
from pymongo.errors import DuplicateKeyError

from feira.banco import banco
from feira.catalogo import devolver_unidades
from feira.erros import ErroApi, validar_corpo

rotas = Blueprint("webhooks", __name__)


class EventoDePagamento(BaseModel):
    evento_id: str = Field(min_length=1)
    pedido_id: str
    tipo: Literal["pago", "recusado"]
    ocorrido_em: AwareDatetime


def exigir_assinatura_valida() -> None:
    segredo = current_app.config["WEBHOOK_SEGREDO"]
    esperada = hmac.new(segredo.encode(), request.get_data(), hashlib.sha256).hexdigest()
    recebida = request.headers.get("X-Assinatura", "").lower()
    if not segredo or not hmac.compare_digest(esperada.encode(), recebida.encode()):
        raise ErroApi(401, "nao_autorizado", "Assinatura do webhook ausente ou inválida.")


def registrar_evento(evento: EventoDePagamento) -> bool:
    try:
        banco().eventos.insert_one(
            {"_id": evento.evento_id, **evento.model_dump(exclude={"evento_id"})}
        )
    except DuplicateKeyError:
        return False
    return True


def aplicar_evento(evento: EventoDePagamento) -> None:
    if not ObjectId.is_valid(evento.pedido_id):
        return
    filtro = {"_id": ObjectId(evento.pedido_id), "status": "aguardando_pagamento"}
    if evento.tipo == "pago":
        banco().pedidos.update_one(
            filtro, {"$set": {"status": "pago", "pago_em": evento.ocorrido_em}}
        )
    elif pedido := banco().pedidos.find_one_and_update(filtro, {"$set": {"status": "cancelado"}}):
        devolver_unidades(pedido["linhas"])


@rotas.post("/v1/webhooks/pagamento")
def receber_pagamento():
    exigir_assinatura_valida()
    evento = validar_corpo(EventoDePagamento)
    if registrar_evento(evento):
        aplicar_evento(evento)
    return {"recebido": True}
