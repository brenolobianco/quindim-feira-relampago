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
