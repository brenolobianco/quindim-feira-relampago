import multiprocessing

from feira.app import create_app

PROCESSOS = 12


def reservar_em_outro_processo(nome_do_banco, barreira, resultados, itens):
    cliente = create_app(MONGO_BANCO=nome_do_banco).test_client()
    corpo = {
        "cliente_id": "cli_concorrente",
        "itens": [{"sku": s, "quantidade": q} for s, q in itens],
    }
    barreira.wait()
    resultados.put(cliente.post("/v1/reservas", json=corpo).status_code)


def disparar_ao_mesmo_tempo(app, pedidos) -> list[int]:
    contexto = multiprocessing.get_context("spawn")
    barreira = contexto.Barrier(len(pedidos))
    resultados = contexto.Queue()
    processos = [
        contexto.Process(
            target=reservar_em_outro_processo,
            args=(app.config["MONGO_BANCO"], barreira, resultados, itens),
        )
        for itens in pedidos
    ]
    for processo in processos:
        processo.start()
    status = [resultados.get(timeout=120) for _ in processos]
    for processo in processos:
        processo.join()
    return status


def unidades_em_reservas(banco) -> dict[str, int]:
    soma: dict[str, int] = {}
    for reserva in banco.reservas.find():
        for item in reserva["itens"]:
            soma[item["sku"]] = soma.get(item["sku"], 0) + item["quantidade"]
    return soma


def assert_nada_vendido_alem_do_estoque(banco):
    reservado = unidades_em_reservas(banco)
    for livro in banco.livros.find():
        assert livro["disponivel"] >= 0
        assert livro["estoque"] - livro["disponivel"] == reservado.get(livro["_id"], 0)


def test_ultima_unidade_disputada_por_varios_processos_vai_para_um_so(app, banco):
    status = disparar_ao_mesmo_tempo(app, [[("QND-005", 1)]] * PROCESSOS)

    assert sorted(status) == [201] + [409] * (PROCESSOS - 1)
    assert banco.livros.find_one({"_id": "QND-005"})["disponivel"] == 0
    assert_nada_vendido_alem_do_estoque(banco)


def test_reservas_simultaneas_com_varios_skus_nunca_passam_do_estoque(app, banco):
    combinacoes = [
        [("QND-004", 2), ("QND-001", 3)],
        [("QND-004", 1), ("QND-005", 1)],
        [("QND-001", 3), ("QND-004", 1)],
        [("QND-005", 1), ("QND-002", 2)],
    ]
    pedidos = [combinacoes[i % len(combinacoes)] for i in range(PROCESSOS)]

    status = disparar_ao_mesmo_tempo(app, pedidos)

    assert set(status) <= {201, 409}
    assert status.count(201) == banco.reservas.count_documents({})
    assert_nada_vendido_alem_do_estoque(banco)
