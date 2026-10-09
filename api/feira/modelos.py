from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer

IdMongo = Annotated[str, BeforeValidator(str)]
DataUTC = Annotated[
    datetime, PlainSerializer(lambda data: data.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))
]


class Livro(BaseModel):
    sku: str = Field(validation_alias="_id")
    titulo: str
    preco_centavos: int
    estoque: int
    disponivel: int


class ItemReservado(BaseModel):
    sku: str
    quantidade: int
    preco_centavos: int


class Reserva(BaseModel):
    id: IdMongo = Field(validation_alias="_id")
    cliente_id: str
    status: str
    itens: list[ItemReservado]
    criado_em: DataUTC
    expira_em: DataUTC
