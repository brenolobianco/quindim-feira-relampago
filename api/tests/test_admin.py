import pytest


@pytest.fixture
def feira_em_andamento(banco):
    banco.livros.update_many({}, {"$set": {"disponivel": 0}})
    for colecao in ("reservas", "pedidos", "eventos"):
        banco[colecao].insert_one({"qualquer": "coisa"})


def test_reset_apaga_tudo_e_restaura_o_seed(app, cliente, banco, feira_em_andamento):
    resposta = cliente.post("/v1/admin/reset", headers={"X-Admin-Token": app.config["ADMIN_TOKEN"]})

    assert resposta.status_code == 204
    assert resposta.get_data() == b""
    for colecao in ("reservas", "pedidos", "eventos"):
        assert banco[colecao].count_documents({}) == 0
    disponiveis = {livro["_id"]: livro["disponivel"] for livro in banco.livros.find()}
    assert disponiveis == {"QND-001": 10, "QND-002": 10, "QND-003": 10, "QND-004": 3, "QND-005": 1}


@pytest.mark.parametrize("cabecalhos", [{}, {"X-Admin-Token": "errado"}, {"X-Admin-Token": ""}])
def test_reset_sem_token_valido_responde_401_e_nao_apaga_nada(
    cliente, banco, feira_em_andamento, cabecalhos
):
    resposta = cliente.post("/v1/admin/reset", headers=cabecalhos)

    assert resposta.status_code == 401
    assert resposta.get_json()["erro"]["codigo"] == "nao_autorizado"
    assert banco.reservas.count_documents({}) == 1
    assert banco.livros.find_one({"_id": "QND-001"})["disponivel"] == 0


def test_reset_recusa_tudo_quando_o_token_nao_esta_configurado(app, feira_em_andamento):
    app.config["ADMIN_TOKEN"] = ""

    resposta = app.test_client().post("/v1/admin/reset", headers={"X-Admin-Token": ""})

    assert resposta.status_code == 401
