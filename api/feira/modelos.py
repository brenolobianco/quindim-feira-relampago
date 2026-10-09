from pydantic import BaseModel, Field


class Livro(BaseModel):
    sku: str = Field(validation_alias="_id")
    titulo: str
    preco_centavos: int
    estoque: int
    disponivel: int
