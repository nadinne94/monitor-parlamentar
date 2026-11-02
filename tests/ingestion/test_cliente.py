import httpx

from monitor.ingestion.core.cliente import ClienteApi

BASE = "https://api.exemplo.gov.br/v2"


def cliente_com(handler, **kwargs) -> ClienteApi:
    return ClienteApi(BASE, transport=httpx.MockTransport(handler), espera_inicial=0, **kwargs)


def test_get_json_devolve_o_corpo_da_resposta():
    def handler(request):
        return httpx.Response(200, json={"dados": [{"id": 1}]})

    with cliente_com(handler) as cliente:
        corpo = cliente.get_json("/deputados")

    assert corpo == {"dados": [{"id": 1}]}
