from feira.pedidos import calcular_linhas


def item(sku: str, quantidade: int, preco_centavos: int) -> dict:
    return {"sku": sku, "quantidade": quantidade, "preco_centavos": preco_centavos}


def test_reproduz_as_linhas_do_exemplo_do_contrato():
    linhas = calcular_linhas(
        [item("QND-001", 1, 3990), item("QND-002", 1, 2990), item("QND-003", 1, 1995)]
    )

    assert linhas == [
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
    ]


def test_valor_da_linha_e_preco_vezes_quantidade():
    linhas = calcular_linhas([item("QND-001", 2, 3990), item("QND-003", 1, 1995)])

    assert [linha["valor_centavos"] for linha in linhas] == [7980, 1995]
    assert [linha["desconto_centavos"] for linha in linhas] == [798, 200]
    assert [linha["liquido_centavos"] for linha in linhas] == [7182, 1795]


def test_faixa_do_desconto_conta_unidades_e_nao_linhas():
    linhas = calcular_linhas([item("QND-001", 3, 3990), item("QND-002", 2, 2990)])

    assert sum(linha["desconto_centavos"] for linha in linhas) == 2693


def test_sem_desconto_o_liquido_e_o_proprio_valor():
    linhas = calcular_linhas([item("QND-004", 2, 8990)])

    assert linhas[0]["desconto_centavos"] == 0
    assert linhas[0]["liquido_centavos"] == 17980
