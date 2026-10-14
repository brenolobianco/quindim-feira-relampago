import re
from datetime import UTC, datetime, timedelta

import pytest
from bson import ObjectId

DATA_ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def reservar(cliente, *itens) -> str:
    corpo = {"cliente_id": "cli_123", "itens": [{"sku": s, "quantidade": q} for s, q in itens]}
    return cliente.post("/v1/reservas", json=corpo).get_json()["id"]


def confirmar(cliente, reserva_id: str):
    return cliente.post(f"/v1/reservas/{reserva_id}/confirmar")


def vencer(banco, reserva_id: str) -> None:
    banco.reservas.update_one(
        {"_id": ObjectId(reserva_id)},
        {"$set": {"expira_em": datetime.now(UTC) - timedelta(seconds=1)}},
    )


def disponivel(banco, sku: str) -> int:
    return banco.livros.find_one({"_id": sku})["disponivel"]


def test_confirmacao_responde_201_com_o_pedido_do_exemplo_do_contrato(cliente):
    reserva_id = reservar(cliente, ("QND-001", 1), ("QND-002", 1), ("QND-003", 1))

    resposta = confirmar(cliente, reserva_id)

    assert resposta.status_code == 201
    pedido = resposta.get_json()
    assert ObjectId.is_valid(pedido["id"])
    assert DATA_ISO_UTC.match(pedido.pop("criado_em"))
    del pedido["id"]
    assert pedido == {
        "reserva_id": reserva_id,
        "cliente_id": "cli_123",
        "status": "aguardando_pagamento",
        "linhas": [
            {
                "sku": "QND-001",
                "quantidade": 1,
                "preco_centavos": 3990,
                "valor_centavos": 3990,
                "desconto_centavos": 399,
                "liquido_centavos": 3591,
            },
            {
                "sku": "QND-002",
                "quantidade": 1,
                "preco_centavos": 2990,
                "valor_centavos": 2990,
                "desconto_centavos": 299,
                "liquido_centavos": 2691,
            },
            {
                "sku": "QND-003",
                "quantidade": 1,
                "preco_centavos": 1995,
                "valor_centavos": 1995,
                "desconto_centavos": 200,
                "liquido_centavos": 1795,
            },
        ],
        "subtotal_centavos": 8975,
        "desconto_centavos": 898,
        "total_centavos": 8077,
        "pago_em": None,
    }


def test_confirmar_de_novo_responde_200_com_o_mesmo_pedido(cliente, banco):
    reserva_id = reservar(cliente, ("QND-001", 2))
    primeira = confirmar(cliente, reserva_id)

    repeticoes = [confirmar(cliente, reserva_id) for _ in range(3)]

    assert [resposta.status_code for resposta in repeticoes] == [200, 200, 200]
    assert all(resposta.get_json() == primeira.get_json() for resposta in repeticoes)
    assert banco.pedidos.count_documents({}) == 1


def test_reserva_confirmada_muda_de_status_e_continua_segurando_as_unidades(cliente, banco):
    reserva_id = reservar(cliente, ("QND-005", 1))

    confirmar(cliente, reserva_id)

    assert cliente.get(f"/v1/reservas/{reserva_id}").get_json()["status"] == "confirmada"
    assert disponivel(banco, "QND-005") == 0


def test_reserva_confirmada_nao_expira_depois_do_prazo(cliente, banco):
    reserva_id = reservar(cliente, ("QND-005", 1))
    pedido = confirmar(cliente, reserva_id).get_json()
    vencer(banco, reserva_id)

    cliente.get("/v1/livros")
    repeticao = confirmar(cliente, reserva_id)

    assert disponivel(banco, "QND-005") == 0
    assert (repeticao.status_code, repeticao.get_json()) == (200, pedido)


def test_confirmar_reserva_expirada_responde_410_e_nao_gera_pedido(cliente, banco):
    reserva_id = reservar(cliente, ("QND-005", 1))
    vencer(banco, reserva_id)

    resposta = confirmar(cliente, reserva_id)

    assert resposta.status_code == 410
    assert resposta.get_json()["erro"]["codigo"] == "reserva_expirada"
    assert banco.pedidos.count_documents({}) == 0
    assert disponivel(banco, "QND-005") == 1


@pytest.mark.parametrize("reserva_id", ["66f0c1d2e4b0a1b2c3d4e5f6", "nao-e-um-id"])
def test_confirmar_reserva_inexistente_ou_id_malformado_responde_404(cliente, reserva_id):
    resposta = confirmar(cliente, reserva_id)

    assert resposta.status_code == 404
    assert resposta.get_json()["erro"]["codigo"] == "nao_encontrado"


def test_consultar_pedido_devolve_o_mesmo_formato_da_confirmacao(cliente):
    pedido = confirmar(cliente, reservar(cliente, ("QND-001", 3))).get_json()

    resposta = cliente.get(f"/v1/pedidos/{pedido['id']}")

    assert (resposta.status_code, resposta.get_json()) == (200, pedido)


@pytest.mark.parametrize("pedido_id", ["66f0c1d2e4b0a1b2c3d4e5f6", "nao-e-um-id"])
def test_consultar_pedido_inexistente_ou_id_malformado_responde_404(cliente, pedido_id):
    resposta = cliente.get(f"/v1/pedidos/{pedido_id}")

    assert resposta.status_code == 404
    assert resposta.get_json()["erro"]["codigo"] == "nao_encontrado"
