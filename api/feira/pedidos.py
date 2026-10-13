from flask import Blueprint
from pymongo import ReturnDocument
from pymongo.database import Database

from feira.banco import banco, buscar_por_id
from feira.catalogo import liberar_reservas_vencidas
from feira.erros import ErroApi
from feira.modelos import Pedido
from feira.reservas import agora

rotas = Blueprint("pedidos", __name__)
rotas.before_request(liberar_reservas_vencidas)


def criar_indices(db: Database) -> None:
    db.pedidos.create_index("reserva_id", unique=True)


def percentual_de_desconto(unidades: int) -> int:
    if unidades >= 5:
        return 15
    if unidades >= 3:
        return 10
    return 0


def calcular_desconto(subtotal_centavos: int, unidades: int) -> int:
    percentual = percentual_de_desconto(unidades)
    return (subtotal_centavos * percentual + 50) // 100


def ratear_desconto(valores_centavos: list[int], desconto_centavos: int) -> list[int]:
    subtotal = sum(valores_centavos)
    proporcoes = [divmod(desconto_centavos * valor, subtotal) for valor in valores_centavos]
    descontos = [parte_inteira for parte_inteira, _ in proporcoes]
    sobra = desconto_centavos - sum(descontos)
    linhas_por_maior_resto = sorted(
        range(len(proporcoes)), key=lambda linha: proporcoes[linha][1], reverse=True
    )
    for linha in linhas_por_maior_resto[:sobra]:
        descontos[linha] += 1
    return descontos


def calcular_linhas(itens: list[dict]) -> list[dict]:
    valores = [item["preco_centavos"] * item["quantidade"] for item in itens]
    unidades = sum(item["quantidade"] for item in itens)
    descontos = ratear_desconto(valores, calcular_desconto(sum(valores), unidades))
    return [
        {
            **item,
            "valor_centavos": valor,
            "desconto_centavos": desconto,
            "liquido_centavos": valor - desconto,
        }
        for item, valor, desconto in zip(itens, valores, descontos, strict=True)
    ]


def montar_pedido(reserva: dict) -> dict:
    linhas = calcular_linhas(reserva["itens"])
    return {
        "reserva_id": reserva["_id"],
        "cliente_id": reserva["cliente_id"],
        "status": "aguardando_pagamento",
        "linhas": linhas,
        "subtotal_centavos": sum(linha["valor_centavos"] for linha in linhas),
        "desconto_centavos": sum(linha["desconto_centavos"] for linha in linhas),
        "total_centavos": sum(linha["liquido_centavos"] for linha in linhas),
        "criado_em": reserva["confirmada_em"],
        "pago_em": None,
    }


@rotas.post("/v1/reservas/<reserva_id>/confirmar")
def confirmar_reserva(reserva_id: str):
    reservas = banco().reservas
    reserva = buscar_por_id(reservas, reserva_id)
    instante = agora()
    confirmou_agora = reservas.update_one(
        {"_id": reserva["_id"], "status": "ativa", "expira_em": {"$gt": instante}},
        {"$set": {"status": "confirmada", "confirmada_em": instante}},
    ).modified_count
    reserva = buscar_por_id(reservas, reserva_id)
    if reserva["status"] != "confirmada":
        raise ErroApi(410, "reserva_expirada", "A reserva expirou e não pode mais ser confirmada.")
    pedido = banco().pedidos.find_one_and_update(
        {"reserva_id": reserva["_id"]},
        {"$setOnInsert": montar_pedido(reserva)},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return Pedido.model_validate(pedido).model_dump(), 201 if confirmou_agora else 200
