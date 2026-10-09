from datetime import UTC, datetime, timedelta

from flask import Blueprint, current_app
from pydantic import BaseModel, ConfigDict, Field, field_validator

from feira.banco import banco, buscar_por_id
from feira.catalogo import SEED
from feira.erros import ErroApi, validar_corpo
from feira.modelos import Reserva

MAXIMO_POR_SKU = 3

rotas = Blueprint("reservas", __name__)


class ItemSolicitado(BaseModel):
    model_config = ConfigDict(strict=True)

    sku: str
    quantidade: int = Field(ge=1, le=MAXIMO_POR_SKU)

    @field_validator("sku")
    @classmethod
    def sku_do_catalogo(cls, sku: str) -> str:
        if sku not in SEED:
            raise ValueError("SKU fora do catálogo")
        return sku


class NovaReserva(BaseModel):
    model_config = ConfigDict(strict=True)

    cliente_id: str = Field(min_length=1)
    itens: list[ItemSolicitado] = Field(min_length=1)

    @field_validator("itens")
    @classmethod
    def sem_sku_repetido(cls, itens: list[ItemSolicitado]) -> list[ItemSolicitado]:
        skus = [item.sku for item in itens]
        if len(skus) != len(set(skus)):
            raise ValueError("SKU repetido na reserva")
        return itens


def agora() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def separar_unidades(itens: list[ItemSolicitado]) -> list[dict]:
    separados, sem_estoque = [], []
    for item in itens:
        livro = banco().livros.find_one_and_update(
            {"_id": item.sku, "disponivel": {"$gte": item.quantidade}},
            {"$inc": {"disponivel": -item.quantidade}},
        )
        if livro is None:
            sem_estoque.append(item.sku)
        else:
            separados.append(
                {
                    "sku": item.sku,
                    "quantidade": item.quantidade,
                    "preco_centavos": livro["preco_centavos"],
                }
            )
    if sem_estoque:
        devolver_unidades(separados)
        raise ErroApi(
            409,
            "estoque_insuficiente",
            "Não há unidades suficientes para reservar.",
            {"skus": sem_estoque},
        )
    return separados


def devolver_unidades(itens: list[dict]) -> None:
    for item in itens:
        banco().livros.update_one(
            {"_id": item["sku"]}, {"$inc": {"disponivel": item["quantidade"]}}
        )


@rotas.post("/v1/reservas")
def criar_reserva():
    pedido = validar_corpo(NovaReserva)
    itens = separar_unidades(pedido.itens)
    criado_em = agora()
    reserva = {
        "cliente_id": pedido.cliente_id,
        "status": "ativa",
        "itens": itens,
        "criado_em": criado_em,
        "expira_em": criado_em + timedelta(seconds=current_app.config["RESERVA_TTL_SEGUNDOS"]),
    }
    banco().reservas.insert_one(reserva)
    return Reserva.model_validate(reserva).model_dump(), 201


@rotas.get("/v1/reservas/<reserva_id>")
def consultar_reserva(reserva_id: str):
    return Reserva.model_validate(buscar_por_id(banco().reservas, reserva_id)).model_dump()
