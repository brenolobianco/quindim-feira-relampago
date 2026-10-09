from feira.catalogo import aplicar_seed


def test_lista_os_livros_do_seed_em_ordem_de_sku(cliente):
    resposta = cliente.get("/v1/livros")

    assert resposta.status_code == 200
    assert resposta.get_json() == {
        "livros": [
            {
                "sku": "QND-001",
                "titulo": "O Jardim de Dentro",
                "preco_centavos": 3990,
                "estoque": 10,
                "disponivel": 10,
            },
            {
                "sku": "QND-002",
                "titulo": "Bicho-Palavra",
                "preco_centavos": 2990,
                "estoque": 10,
                "disponivel": 10,
            },
            {
                "sku": "QND-003",
                "titulo": "A Casa que Anda",
                "preco_centavos": 1995,
                "estoque": 10,
                "disponivel": 10,
            },
            {
                "sku": "QND-004",
                "titulo": "Kit Primeira Leitura",
                "preco_centavos": 8990,
                "estoque": 3,
                "disponivel": 3,
            },
            {
                "sku": "QND-005",
                "titulo": "A Lua no Bolso — edição numerada",
                "preco_centavos": 12900,
                "estoque": 1,
                "disponivel": 1,
            },
        ]
    }


def test_seed_aplicado_de_novo_nao_duplica_nem_desfaz_o_disponivel(banco):
    banco.livros.update_one({"_id": "QND-004"}, {"$set": {"disponivel": 1}})

    aplicar_seed(banco)

    assert banco.livros.count_documents({}) == 5
    assert banco.livros.find_one({"_id": "QND-004"})["disponivel"] == 1
