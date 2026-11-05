import httpx
import pytest

from monitor.ingestion.core.cliente import USER_AGENT, ClienteApi, segundos_pedidos_pela_api

BASE = "https://api.exemplo.gov.br/v2"


@pytest.mark.parametrize(
    ("cabecalhos", "esperado"),
    [
        ({"Retry-After": "30"}, 30.0),
        ({"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}, 0.0),
        ({}, 0.0),
    ],
)
def test_segundos_pedidos_pela_api(cabecalhos, esperado):
    requisicao = httpx.Request("GET", f"{BASE}/deputados")
    resposta = httpx.Response(503, headers=cabecalhos, request=requisicao)
    erro = httpx.HTTPStatusError("503", request=requisicao, response=resposta)

    assert segundos_pedidos_pela_api(erro) == esperado


def test_segundos_pedidos_pela_api_ignora_erros_de_rede():
    assert segundos_pedidos_pela_api(httpx.ConnectError("sem rede")) == 0.0


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


def pagina(dados, proxima=None):
    links = [{"rel": "self", "href": "..."}]
    if proxima:
        links.append({"rel": "next", "href": proxima})
    return {"dados": dados, "links": links}


def test_paginar_uma_pagina():
    def handler(request):
        return httpx.Response(200, json=pagina([{"id": 1}, {"id": 2}]))

    with cliente_com(handler) as cliente:
        itens = list(cliente.paginar("/deputados"))

    assert itens == [{"id": 1}, {"id": 2}]


def test_paginar_segue_o_link_next():
    paginas = {
        "1": pagina([{"id": 1}], proxima=f"{BASE}/deputados?pagina=2&itens=1"),
        "2": pagina([{"id": 2}], proxima=f"{BASE}/deputados?pagina=3&itens=1"),
        "3": pagina([{"id": 3}]),
    }

    def handler(request):
        return httpx.Response(200, json=paginas[request.url.params.get("pagina", "1")])

    with cliente_com(handler) as cliente:
        itens = list(cliente.paginar("/deputados", {"itens": 1}))

    assert itens == [{"id": 1}, {"id": 2}, {"id": 3}]


def test_paginar_resposta_vazia_nao_e_erro():
    def handler(request):
        return httpx.Response(200, json=pagina([]))

    with cliente_com(handler) as cliente:
        assert list(cliente.paginar("/deputados")) == []


def cliente_que_anota_esperas(handler, esperas, **kwargs) -> ClienteApi:
    return ClienteApi(BASE, transport=httpx.MockTransport(handler), dormir=esperas.append, **kwargs)


def test_espera_cresce_exponencialmente():
    esperas = []

    def handler(request):
        return httpx.Response(503)

    with (
        cliente_que_anota_esperas(handler, esperas, max_tentativas=4) as cliente,
        pytest.raises(httpx.HTTPStatusError),
    ):
        cliente.get_json("/deputados")

    assert esperas == [2.0, 4.0, 8.0]


def test_respeita_o_retry_after_da_api():
    esperas = []
    respostas = iter(
        [httpx.Response(503, headers={"Retry-After": "30"}), httpx.Response(200, json={})]
    )

    with cliente_que_anota_esperas(lambda request: next(respostas), esperas) as cliente:
        cliente.get_json("/deputados")

    assert esperas == [30.0]


def test_espera_tem_teto():
    esperas = []
    respostas = iter(
        [httpx.Response(503, headers={"Retry-After": "600"}), httpx.Response(200, json={})]
    )

    with cliente_que_anota_esperas(lambda request: next(respostas), esperas) as cliente:
        cliente.get_json("/deputados")

    assert esperas == [60.0]


def test_padrao_faz_cinco_tentativas():
    chamadas = []

    def handler(request):
        chamadas.append(request)
        return httpx.Response(503)

    with cliente_que_anota_esperas(handler, []) as cliente, pytest.raises(httpx.HTTPStatusError):
        cliente.get_json("/deputados")

    assert len(chamadas) == 5
