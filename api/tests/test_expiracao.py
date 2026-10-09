from datetime import UTC, datetime, timedelta

from bson import ObjectId


def reservar_ultima_lua(cliente) -> str:
    corpo = {"cliente_id": "cli_123", "itens": [{"sku": "QND-005", "quantidade": 1}]}
    resposta = cliente.post("/v1/reservas", json=corpo)
    assert resposta.status_code == 201
    return resposta.get_json()["id"]


def mudar_expiracao(banco, reserva_id: str, segundos_a_partir_de_agora: int) -> None:
    banco.reservas.update_one(
        {"_id": ObjectId(reserva_id)},
        {"$set": {"expira_em": datetime.now(UTC) + timedelta(seconds=segundos_a_partir_de_agora)}},
    )


def disponivel_da_lua(cliente) -> int:
    livros = cliente.get("/v1/livros").get_json()["livros"]
    return next(livro["disponivel"] for livro in livros if livro["sku"] == "QND-005")


def test_reserva_dentro_do_prazo_continua_segurando_as_unidades(cliente, banco):
    reserva_id = reservar_ultima_lua(cliente)
    mudar_expiracao(banco, reserva_id, 60)

    assert disponivel_da_lua(cliente) == 0
    assert banco.reservas.find_one({"_id": ObjectId(reserva_id)})["status"] == "ativa"


def test_unidades_de_reserva_vencida_voltam_no_proximo_get_de_livros(cliente, banco):
    reserva_id = reservar_ultima_lua(cliente)
    mudar_expiracao(banco, reserva_id, -1)

    assert disponivel_da_lua(cliente) == 1
    assert banco.reservas.find_one({"_id": ObjectId(reserva_id)})["status"] == "expirada"


def test_nova_reserva_aproveita_as_unidades_de_uma_reserva_vencida(cliente, banco):
    mudar_expiracao(banco, reservar_ultima_lua(cliente), -1)

    reservar_ultima_lua(cliente)

    assert disponivel_da_lua(cliente) == 0


def test_unidades_de_reserva_vencida_voltam_uma_unica_vez(cliente, banco):
    mudar_expiracao(banco, reservar_ultima_lua(cliente), -1)

    for _ in range(3):
        cliente.get("/v1/livros")

    assert disponivel_da_lua(cliente) == 1


def test_libera_todas_as_reservas_vencidas_de_uma_vez(cliente, banco):
    corpo = {"cliente_id": "cli_123", "itens": [{"sku": "QND-001", "quantidade": 3}]}
    ids = [cliente.post("/v1/reservas", json=corpo).get_json()["id"] for _ in range(3)]
    for reserva_id in ids:
        mudar_expiracao(banco, reserva_id, -1)

    livros = cliente.get("/v1/livros").get_json()["livros"]

    assert (livros[0]["sku"], livros[0]["disponivel"]) == ("QND-001", 10)
    assert banco.reservas.count_documents({"status": "expirada"}) == 3
