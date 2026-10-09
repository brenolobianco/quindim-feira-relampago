from pydantic import BaseModel, ConfigDict, Field, field_validator

from feira.catalogo import SEED

MAXIMO_POR_SKU = 3


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
