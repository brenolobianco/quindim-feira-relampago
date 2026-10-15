import hashlib
import hmac
from typing import Literal

from flask import Blueprint, current_app, request
from pydantic import AwareDatetime, BaseModel, Field

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
    recebida = request.headers.get("X-Assinatura", "")
    if not segredo or not hmac.compare_digest(esperada.encode(), recebida.encode()):
        raise ErroApi(401, "nao_autorizado", "Assinatura do webhook ausente ou inválida.")


@rotas.post("/v1/webhooks/pagamento")
def receber_pagamento():
    exigir_assinatura_valida()
    validar_corpo(EventoDePagamento)
    return {"recebido": True}
