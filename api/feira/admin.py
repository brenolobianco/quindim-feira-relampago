import hmac

from flask import Blueprint, current_app, request

from feira.banco import banco
from feira.catalogo import aplicar_seed
from feira.erros import ErroApi

rotas = Blueprint("admin", __name__)


def exigir_token_de_admin() -> None:
    esperado = current_app.config["ADMIN_TOKEN"]
    recebido = request.headers.get("X-Admin-Token", "")
    if not esperado or not hmac.compare_digest(esperado.encode(), recebido.encode()):
        raise ErroApi(401, "nao_autorizado", "Token de admin ausente ou inválido.")


@rotas.post("/v1/admin/reset")
def resetar():
    exigir_token_de_admin()
    db = banco()
    for colecao in ("reservas", "pedidos", "eventos", "livros"):
        db[colecao].delete_many({})
    aplicar_seed(db)
    return "", 204
