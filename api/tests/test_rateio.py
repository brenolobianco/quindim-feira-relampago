from itertools import product

from feira.catalogo import SEED
from feira.pedidos import calcular_desconto, ratear_desconto


def test_reproduz_o_exemplo_do_contrato():
    assert ratear_desconto([3990, 2990, 1995], 898) == [399, 299, 200]


def test_centavo_que_sobra_vai_para_a_linha_de_maior_resto():
    assert ratear_desconto([1000, 3000], 101) == [25, 76]


def test_empate_de_resto_favorece_a_linha_que_aparece_primeiro():
    assert ratear_desconto([1000, 1000, 1000], 100) == [34, 33, 33]


def test_distribui_mais_de_um_centavo_de_sobra_um_por_linha():
    assert ratear_desconto([1000, 1000, 1000], 200) == [67, 67, 66]


def test_linha_unica_recebe_o_desconto_inteiro():
    assert ratear_desconto([5985], 599) == [599]


def test_sem_desconto_todas_as_linhas_ficam_zeradas():
    assert ratear_desconto([3990, 2990], 0) == [0, 0]


def test_soma_das_linhas_e_o_desconto_total_em_qualquer_carrinho_do_catalogo():
    precos = [livro["preco_centavos"] for livro in SEED.values()]
    for quantidades in product(range(4), repeat=len(precos)):
        valores = [
            preco * quantidade
            for preco, quantidade in zip(precos, quantidades, strict=True)
            if quantidade
        ]
        if not valores:
            continue
        desconto = calcular_desconto(sum(valores), unidades=sum(quantidades))

        assert sum(ratear_desconto(valores, desconto)) == desconto
