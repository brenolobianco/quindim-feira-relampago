import hashlib
import hmac

import pytest

from feira.app import create_app

SEGREDO_DO_EXEMPLO = "segredo-de-exemplo"
CORPO_DO_EXEMPLO = (
    b'{"evento_id":"evt_0001","pedido_id":"66f0c2a1e4b0a1b2c3d4e5f7",'
    b'"tipo":"pago","ocorrido_em":"2026-10-01T12:00:00Z"}'
)
ASSINATURA_DO_EXEMPLO = "bcb4b6f50d0ad32b6e2988d50fca256a72fd31196164ea4c210214966da968d7"


def enviar(cliente, corpo: bytes, assinatura: str | None):
    cabecalhos = {"Content-Type": "application/json"}
    if assinatura is not None:
        cabecalhos["X-Assinatura"] = assinatura
    return cliente.post("/v1/webhooks/pagamento", data=corpo, headers=cabecalhos)


def assinar(corpo: bytes) -> str:
    return hmac.new(SEGREDO_DO_EXEMPLO.encode(), corpo, hashlib.sha256).hexdigest()


def test_vetor_do_contrato_e_aceito(cliente):
    resposta = enviar(cliente, CORPO_DO_EXEMPLO, ASSINATURA_DO_EXEMPLO)

    assert (resposta.status_code, resposta.get_json()) == (200, {"recebido": True})


@pytest.mark.parametrize(
    "corpo, assinatura",
    [
        (CORPO_DO_EXEMPLO, None),
        (CORPO_DO_EXEMPLO, ""),
        (CORPO_DO_EXEMPLO, "0" * 64),
        (CORPO_DO_EXEMPLO.replace(b"pago", b"recusado"), ASSINATURA_DO_EXEMPLO),
        (CORPO_DO_EXEMPLO, "assinatura-ção"),
    ],
)
def test_assinatura_ausente_ou_invalida_responde_401(cliente, corpo, assinatura):
    resposta = enviar(cliente, corpo, assinatura)

    assert resposta.status_code == 401
    assert resposta.get_json()["erro"]["codigo"] == "nao_autorizado"


def test_sem_segredo_configurado_nenhuma_assinatura_vale():
    app = create_app(MONGO_BANCO="feira_teste", WEBHOOK_SEGREDO="")
    vazio = hmac.new(b"", CORPO_DO_EXEMPLO, hashlib.sha256).hexdigest()

    resposta = enviar(app.test_client(), CORPO_DO_EXEMPLO, vazio)

    assert resposta.status_code == 401


def test_corpo_assinado_fora_do_contrato_responde_400(cliente):
    corpo = b'{"evento_id":"evt_0002","pedido_id":"x","tipo":"estornado"}'

    resposta = enviar(cliente, corpo, assinar(corpo))

    assert resposta.status_code == 400
    assert resposta.get_json()["erro"]["codigo"] == "requisicao_invalida"


@pytest.fixture
def pedido_id(cliente) -> str:
    corpo = {"cliente_id": "cli_123", "itens": [{"sku": "QND-005", "quantidade": 1}]}
    reserva_id = cliente.post("/v1/reservas", json=corpo).get_json()["id"]
    return cliente.post(f"/v1/reservas/{reserva_id}/confirmar").get_json()["id"]


def notificar(cliente, evento_id: str, pedido_id: str, tipo: str):
    corpo = (
        f'{{"evento_id":"{evento_id}","pedido_id":"{pedido_id}",'
        f'"tipo":"{tipo}","ocorrido_em":"2026-10-01T12:00:00Z"}}'
    ).encode()
    return enviar(cliente, corpo, assinar(corpo))


def consultar(cliente, pedido_id: str) -> dict:
    return cliente.get(f"/v1/pedidos/{pedido_id}").get_json()


def disponivel(banco) -> int:
    return banco.livros.find_one({"_id": "QND-005"})["disponivel"]


def test_pago_leva_o_pedido_a_pago_com_a_data_do_evento(cliente, banco, pedido_id):
    resposta = notificar(cliente, "evt_1", pedido_id, "pago")

    assert (resposta.status_code, resposta.get_json()) == (200, {"recebido": True})
    pedido = consultar(cliente, pedido_id)
    assert (pedido["status"], pedido["pago_em"]) == ("pago", "2026-10-01T12:00:00Z")
    assert disponivel(banco) == 0


def test_recusas_repetidas_cancelam_e_devolvem_as_unidades_uma_vez(cliente, banco, pedido_id):
    respostas = [notificar(cliente, f"evt_{n}", pedido_id, "recusado") for n in range(3)]

    assert [resposta.status_code for resposta in respostas] == [200, 200, 200]
    assert consultar(cliente, pedido_id)["status"] == "cancelado"
    assert disponivel(banco) == 1


@pytest.mark.parametrize(
    "primeiro, depois, status_final",
    [("pago", "recusado", "pago"), ("recusado", "pago", "cancelado")],
)
def test_status_final_nao_muda_com_eventos_fora_de_ordem(
    cliente, banco, pedido_id, primeiro, depois, status_final
):
    notificar(cliente, "evt_1", pedido_id, primeiro)

    resposta = notificar(cliente, "evt_2", pedido_id, depois)

    assert resposta.status_code == 200
    pedido = consultar(cliente, pedido_id)
    assert pedido["status"] == status_final
    assert disponivel(banco) == (1 if status_final == "cancelado" else 0)


def test_mesmo_evento_id_nao_e_aplicado_duas_vezes(cliente, banco, pedido_id):
    notificar(cliente, "evt_1", "66f0c2a1e4b0a1b2c3d4e5f7", "recusado")

    resposta = notificar(cliente, "evt_1", pedido_id, "recusado")

    assert resposta.status_code == 200
    assert consultar(cliente, pedido_id)["status"] == "aguardando_pagamento"
    assert banco.eventos.count_documents({}) == 1


@pytest.mark.parametrize("pedido_id", ["66f0c2a1e4b0a1b2c3d4e5f7", "nao-e-um-id"])
def test_evento_de_pedido_inexistente_responde_200(cliente, pedido_id):
    resposta = notificar(cliente, "evt_1", pedido_id, "pago")

    assert (resposta.status_code, resposta.get_json()) == (200, {"recebido": True})


def test_vetor_do_contrato_sem_content_type_tambem_e_aceito(cliente):
    resposta = cliente.post(
        "/v1/webhooks/pagamento",
        data=CORPO_DO_EXEMPLO,
        headers={"X-Assinatura": ASSINATURA_DO_EXEMPLO},
    )

    assert (resposta.status_code, resposta.get_json()) == (200, {"recebido": True})


def test_assinatura_em_hexadecimal_maiusculo_tambem_vale(cliente):
    resposta = enviar(cliente, CORPO_DO_EXEMPLO, ASSINATURA_DO_EXEMPLO.upper())

    assert resposta.status_code == 200
