import httpx

from monitor.ingestion.camara.deputados import URL_API_CAMARA
from monitor.ingestion.camara.despesas import buscar_despesas
from monitor.ingestion.core.cliente import ClienteApi


def despesa(cod="8166223", mes=10, documento="12345678000199"):
    """Um item no formato de `/deputados/{id}/despesas`, com fornecedor fictício."""
    return {
        "ano": 2026,
        "mes": mes,
        "tipoDespesa": "COMBUSTÍVEIS E LUBRIFICANTES.",
        "codDocumento": cod,
        "dataDocumento": f"2026-{mes:02d}-05T00:00:00",
        "valorDocumento": 150.0,
        "valorGlosa": 0.0,
        "valorLiquido": -150.0,
        "nomeFornecedor": "POSTO EXEMPLO LTDA",
        "cnpjCpfFornecedor": documento,
    }


def cliente_falso(rotas, recebidas=None):
    """Cliente que responde a cada caminho com os dados da rota correspondente (404 fora delas)."""

    def handler(request):
        if recebidas is not None:
            recebidas.append(request)
        caminho = request.url.path.removeprefix("/api/v2")
        if caminho not in rotas:
            return httpx.Response(404)
        return httpx.Response(200, json={"dados": rotas[caminho], "links": []})

    return ClienteApi(URL_API_CAMARA, transport=httpx.MockTransport(handler), espera_inicial=0)


def test_busca_as_despesas_do_deputado_com_ano_e_mes():
    recebidas = []

    with cliente_falso({"/deputados/74646/despesas": [despesa()]}, recebidas) as cliente:
        despesas = buscar_despesas(cliente, 74646, "2026-10")

    params = recebidas[0].url.params
    assert params["ano"] == "2026"
    assert params["mes"] == "10"
    assert params["itens"] == "100"
    assert [d.cod_documento for d in despesas] == ["8166223"]
