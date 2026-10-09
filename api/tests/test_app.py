from feira.app import create_app


def test_healthz_responde_ok_quando_fala_com_o_mongo(cliente):
    resposta = cliente.get("/healthz")

    assert resposta.status_code == 200
    assert resposta.get_json() == {"status": "ok"}


def test_healthz_responde_503_quando_o_mongo_esta_fora():
    cliente = create_app(MONGO_URL="mongodb://127.0.0.1:1").test_client()

    resposta = cliente.get("/healthz")

    assert resposta.status_code == 503
    assert resposta.get_json()["erro"]["codigo"] == "banco_indisponivel"


def test_rota_inexistente_responde_404_no_formato_de_erro(cliente):
    resposta = cliente.get("/v1/nao-existe")

    assert resposta.status_code == 404
    assert resposta.get_json() == {
        "erro": {
            "codigo": "nao_encontrado",
            "mensagem": "Recurso não encontrado.",
            "detalhes": {},
        }
    }


def test_metodo_nao_permitido_tambem_responde_json(cliente):
    resposta = cliente.post("/healthz")

    assert resposta.status_code == 405
    assert resposta.get_json()["erro"]["codigo"] == "metodo_nao_permitido"


def test_erro_inesperado_responde_500_em_json_sem_stack_trace(app):
    app.add_url_rule("/explode", view_func=lambda: 1 // 0)

    resposta = app.test_client().get("/explode")

    assert resposta.status_code == 500
    assert resposta.is_json
    assert resposta.get_json()["erro"]["codigo"] == "erro_interno"
    assert "Traceback" not in resposta.get_data(as_text=True)
