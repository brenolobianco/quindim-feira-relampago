import pytest

from feira.pedidos import calcular_desconto, percentual_de_desconto


@pytest.mark.parametrize(
    ("unidades", "percentual"), [(1, 0), (2, 0), (3, 10), (4, 10), (5, 15), (9, 15)]
)
def test_percentual_progressivo_pelo_total_de_unidades(unidades, percentual):
    assert percentual_de_desconto(unidades) == percentual


def test_reproduz_o_exemplo_do_contrato():
    assert calcular_desconto(8975, unidades=3) == 898


def test_meio_centavo_arredonda_para_cima():
    assert calcular_desconto(5985, unidades=3) == 599


def test_aplica_quinze_por_cento_a_partir_de_cinco_unidades():
    assert calcular_desconto(17950, unidades=5) == 2693


def test_ate_duas_unidades_nao_tem_desconto():
    assert calcular_desconto(8000, unidades=2) == 0
