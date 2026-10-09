import re
from datetime import datetime, timedelta

from bson import ObjectId

DATA_ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def reservar(cliente, *itens):
    corpo = {"cliente_id": "cli_123", "itens": [{"sku": s, "quantidade": q} for s, q in itens]}
    return cliente.post("/v1/reservas", json=corpo)


def disponiveis(banco) -> dict[str, int]:
    return {livro["_id"]: livro["disponivel"] for livro in banco.livros.find()}


def test_reserva_responde_201_no_formato_do_contrato(cliente):
    resposta = reservar(cliente, ("QND-001", 2), ("QND-003", 1))

    assert resposta.status_code == 201
    reserva = resposta.get_json()
    assert ObjectId.is_valid(reserva["id"])
    assert reserva["cliente_id"] == "cli_123"
    assert reserva["status"] == "ativa"
    assert reserva["itens"] == [
        {"sku": "QND-001", "quantidade": 2, "preco_centavos": 3990},
        {"sku": "QND-003", "quantidade": 1, "preco_centavos": 1995},
    ]
    assert DATA_ISO_UTC.match(reserva["criado_em"])
    assert DATA_ISO_UTC.match(reserva["expira_em"])


def test_reserva_dura_o_ttl_configurado(app, cliente):
    app.config["RESERVA_TTL_SEGUNDOS"] = 600

    reserva = reservar(cliente, ("QND-001", 1)).get_json()

    criado_em = datetime.fromisoformat(reserva["criado_em"])
    expira_em = datetime.fromisoformat(reserva["expira_em"])
    assert expira_em - criado_em == timedelta(seconds=600)


def test_reserva_desconta_do_disponivel_e_nao_do_estoque(cliente, banco):
    reservar(cliente, ("QND-001", 2), ("QND-003", 1))

    livro = banco.livros.find_one({"_id": "QND-001"})
    assert (livro["estoque"], livro["disponivel"]) == (10, 8)
    assert banco.livros.find_one({"_id": "QND-003"})["disponivel"] == 9


def test_reserva_fica_gravada_no_banco(cliente, banco):
    reserva = reservar(cliente, ("QND-002", 3)).get_json()

    gravada = banco.reservas.find_one({"_id": ObjectId(reserva["id"])})
    assert gravada["status"] == "ativa"
    assert gravada["itens"] == [{"sku": "QND-002", "quantidade": 3, "preco_centavos": 2990}]


def test_ultima_unidade_so_pode_ser_reservada_uma_vez(cliente):
    primeira = reservar(cliente, ("QND-005", 1))
    segunda = reservar(cliente, ("QND-005", 1))

    assert primeira.status_code == 201
    assert segunda.status_code == 409
    assert segunda.get_json()["erro"] == {
        "codigo": "estoque_insuficiente",
        "mensagem": "Não há unidades suficientes para reservar.",
        "detalhes": {"skus": ["QND-005"]},
    }


def test_falta_em_um_sku_nao_reserva_nenhum_e_devolve_o_que_ja_tinha_separado(cliente, banco):
    antes = disponiveis(banco)

    resposta = reservar(cliente, ("QND-001", 3), ("QND-002", 1), ("QND-005", 2))

    assert resposta.status_code == 409
    assert resposta.get_json()["erro"]["detalhes"] == {"skus": ["QND-005"]}
    assert disponiveis(banco) == antes
    assert banco.reservas.count_documents({}) == 0


def test_409_lista_todos_os_skus_sem_unidades_suficientes(cliente, banco):
    reservar(cliente, ("QND-004", 3))
    antes = disponiveis(banco)

    resposta = reservar(cliente, ("QND-004", 1), ("QND-001", 1), ("QND-005", 2))

    assert resposta.get_json()["erro"]["detalhes"] == {"skus": ["QND-004", "QND-005"]}
    assert disponiveis(banco) == antes


def test_corpo_invalido_responde_400_sem_tocar_no_estoque(cliente, banco):
    antes = disponiveis(banco)

    resposta = reservar(cliente, ("QND-001", 4))

    assert resposta.status_code == 400
    assert resposta.get_json()["erro"]["codigo"] == "requisicao_invalida"
    assert disponiveis(banco) == antes
