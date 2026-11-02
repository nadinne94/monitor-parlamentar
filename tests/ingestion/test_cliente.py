import httpx
import pytest

from monitor.ingestion.core.cliente import USER_AGENT, ClienteApi

BASE = "https://api.exemplo.gov.br/v2"


def cliente_com(handler, **kwargs) -> ClienteApi:
    return ClienteApi(BASE, transport=httpx.MockTransport(handler), espera_inicial=0, **kwargs)


def test_get_json_devolve_o_corpo_da_resposta():
    def handler(request):
        return httpx.Response(200, json={"dados": [{"id": 1}]})

    with cliente_com(handler) as cliente:
        corpo = cliente.get_json("/deputados")

    assert corpo == {"dados": [{"id": 1}]}


def test_get_json_envia_parametros_e_cabecalhos():
    recebidas = []

    def handler(request):
        recebidas.append(request)
        return httpx.Response(200, json={})

    with cliente_com(handler) as cliente:
        cliente.get_json("/deputados", {"siglaUf": "MG", "itens": 100})

    requisicao = recebidas[0]
    assert requisicao.url.path == "/v2/deputados"
    assert requisicao.url.params["siglaUf"] == "MG"
    assert requisicao.url.params["itens"] == "100"
    assert requisicao.headers["Accept"] == "application/json"
    assert requisicao.headers["User-Agent"] == USER_AGENT


@pytest.mark.parametrize("status", [429, 500, 503])
def test_tenta_de_novo_apos_falha_temporaria(status):
    respostas = iter([httpx.Response(status), httpx.Response(200, json={"ok": True})])
    chamadas = []

    def handler(request):
        chamadas.append(request)
        return next(respostas)

    with cliente_com(handler) as cliente:
        corpo = cliente.get_json("/deputados")

    assert corpo == {"ok": True}
    assert len(chamadas) == 2


def test_tenta_de_novo_apos_erro_de_conexao():
    chamadas = []

    def handler(request):
        chamadas.append(request)
        if len(chamadas) == 1:
            raise httpx.ConnectError("conexão recusada")
        return httpx.Response(200, json={"ok": True})

    with cliente_com(handler) as cliente:
        corpo = cliente.get_json("/deputados")

    assert corpo == {"ok": True}
    assert len(chamadas) == 2


def test_erro_definitivo_falha_sem_nova_tentativa():
    chamadas = []

    def handler(request):
        chamadas.append(request)
        return httpx.Response(404)

    with cliente_com(handler) as cliente, pytest.raises(httpx.HTTPStatusError):
        cliente.get_json("/nao-existe")

    assert len(chamadas) == 1


def test_desiste_depois_do_maximo_de_tentativas():
    chamadas = []

    def handler(request):
        chamadas.append(request)
        return httpx.Response(503)

    with cliente_com(handler, max_tentativas=3) as cliente, pytest.raises(httpx.HTTPStatusError):
        cliente.get_json("/deputados")

    assert len(chamadas) == 3
