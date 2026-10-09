import pytest
from flask import Flask

from feira.erros import ErroApi, validar_corpo
from feira.reservas import NovaReserva


def validar(corpo=None, **contexto):
    with Flask(__name__).test_request_context(method="POST", json=corpo, **contexto):
        return validar_corpo(NovaReserva)


def campos_com_erro(corpo=None, **contexto) -> list[str]:
    with pytest.raises(ErroApi) as erro:
        validar(corpo, **contexto)
    assert erro.value.status == 400
    assert erro.value.codigo == "requisicao_invalida"
    return [falha["campo"] for falha in erro.value.detalhes["campos"]]


def test_aceita_o_corpo_do_exemplo_do_contrato():
    reserva = validar(
        {
            "cliente_id": "cli_123",
            "itens": [{"sku": "QND-001", "quantidade": 2}, {"sku": "QND-003", "quantidade": 1}],
        }
    )

    assert reserva.cliente_id == "cli_123"
    assert [(item.sku, item.quantidade) for item in reserva.itens] == [
        ("QND-001", 2),
        ("QND-003", 1),
    ]


def test_aceita_o_limite_de_tres_unidades_por_sku():
    reserva = validar({"cliente_id": "c", "itens": [{"sku": "QND-005", "quantidade": 3}]})

    assert reserva.itens[0].quantidade == 3


@pytest.mark.parametrize("quantidade", [0, -1, 4, True, "2", 2.0, None])
def test_recusa_quantidade_fora_de_1_a_3_ou_que_nao_e_inteiro(quantidade):
    corpo = {"cliente_id": "c", "itens": [{"sku": "QND-001", "quantidade": quantidade}]}

    assert campos_com_erro(corpo) == ["itens.0.quantidade"]


def test_recusa_sku_fora_do_catalogo():
    corpo = {"cliente_id": "c", "itens": [{"sku": "QND-999", "quantidade": 1}]}

    assert campos_com_erro(corpo) == ["itens.0.sku"]


def test_recusa_o_mesmo_sku_repetido_na_reserva():
    corpo = {
        "cliente_id": "c",
        "itens": [{"sku": "QND-001", "quantidade": 2}, {"sku": "QND-001", "quantidade": 2}],
    }

    assert campos_com_erro(corpo) == ["itens"]


@pytest.mark.parametrize(
    ("corpo", "campo"),
    [
        ({"cliente_id": "c", "itens": []}, "itens"),
        ({"cliente_id": "c"}, "itens"),
        ({"cliente_id": "", "itens": [{"sku": "QND-001", "quantidade": 1}]}, "cliente_id"),
        ({"cliente_id": 123, "itens": [{"sku": "QND-001", "quantidade": 1}]}, "cliente_id"),
        ({"itens": [{"sku": "QND-001", "quantidade": 1}]}, "cliente_id"),
    ],
)
def test_recusa_cliente_ou_itens_ausentes_ou_vazios(corpo, campo):
    assert campos_com_erro(corpo) == [campo]


def test_recusa_corpo_que_nao_e_json():
    assert campos_com_erro(data="isto não é json", content_type="application/json") == [""]


def test_recusa_corpo_json_que_nao_e_objeto():
    assert campos_com_erro([1, 2, 3]) == [""]
