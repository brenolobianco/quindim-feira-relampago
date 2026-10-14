import multiprocessing
from datetime import UTC, datetime

from bson import ObjectId

from feira.app import create_app

PROCESSOS = 12


def requisitar_em_outro_processo(nome_do_banco, barreira, resultados, caminho, corpo):
    cliente = create_app(MONGO_BANCO=nome_do_banco).test_client()
    barreira.wait()
    resposta = cliente.post(caminho, json=corpo)
    resultados.put((resposta.status_code, resposta.get_json()))


def disparar_ao_mesmo_tempo(app, requisicoes) -> list[tuple[int, dict]]:
    contexto = multiprocessing.get_context("spawn")
    barreira = contexto.Barrier(len(requisicoes))
    resultados = contexto.Queue()
    processos = [
        contexto.Process(
            target=requisitar_em_outro_processo,
            args=(app.config["MONGO_BANCO"], barreira, resultados, caminho, corpo),
        )
        for caminho, corpo in requisicoes
    ]
    for processo in processos:
        processo.start()
    respostas = [resultados.get(timeout=120) for _ in processos]
    for processo in processos:
        processo.join()
    return respostas


def corpo_de_reserva(itens) -> dict:
    return {
        "cliente_id": "cli_concorrente",
        "itens": [{"sku": s, "quantidade": q} for s, q in itens],
    }


def reservar_ao_mesmo_tempo(app, pedidos) -> list[int]:
    requisicoes = [("/v1/reservas", corpo_de_reserva(itens)) for itens in pedidos]
    return [status for status, _ in disparar_ao_mesmo_tempo(app, requisicoes)]


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
    status = reservar_ao_mesmo_tempo(app, [[("QND-005", 1)]] * PROCESSOS)

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

    status = reservar_ao_mesmo_tempo(app, pedidos)

    assert set(status) <= {201, 409}
    assert status.count(201) == banco.reservas.count_documents({})
    assert_nada_vendido_alem_do_estoque(banco)


def reservar(cliente, itens) -> str:
    return cliente.post("/v1/reservas", json=corpo_de_reserva(itens)).get_json()["id"]


def confirmacao(reserva_id: str) -> tuple[str, None]:
    return (f"/v1/reservas/{reserva_id}/confirmar", None)


def test_confirmacoes_simultaneas_da_mesma_reserva_geram_um_unico_pedido(app, cliente, banco):
    reserva_id = reservar(cliente, [("QND-001", 3)])

    respostas = disparar_ao_mesmo_tempo(app, [confirmacao(reserva_id)] * PROCESSOS)

    assert sorted(status for status, _ in respostas) == [200] * (PROCESSOS - 1) + [201]
    assert len({pedido["id"] for _, pedido in respostas}) == 1
    assert banco.pedidos.count_documents({}) == 1


def test_upserts_simultaneos_do_pedido_nao_duplicam_nem_dao_erro(app, cliente, banco):
    reserva_id = reservar(cliente, [("QND-001", 3)])
    banco.reservas.update_one(
        {"_id": ObjectId(reserva_id)},
        {"$set": {"status": "confirmada", "confirmada_em": datetime.now(UTC)}},
    )

    respostas = disparar_ao_mesmo_tempo(app, [confirmacao(reserva_id)] * PROCESSOS)

    assert {status for status, _ in respostas} == {200}
    assert banco.pedidos.count_documents({}) == 1
