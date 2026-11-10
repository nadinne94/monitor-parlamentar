import httpx
import pytest

from monitor.ingestion.camara.deputados import URL_API_CAMARA
from monitor.ingestion.camara.votacoes import buscar_votacoes
from monitor.ingestion.core.cliente import ClienteApi
from monitor.ingestion.core.erros import IngestaoError


def votacao(id_, data="2026-10-14T20:56:14", aprovacao=1):
    return {
        "id": id_,
        "dataHoraRegistro": data,
        "siglaOrgao": "PLEN",
        "descricao": f"Votação {id_}",
        "aprovacao": aprovacao,
    }


def cliente_falso(rotas, recebidas=None):
    """Cliente que responde a cada caminho com os dados da rota correspondente."""

    def handler(request):
        if recebidas is not None:
            recebidas.append(request)
        caminho = request.url.path.removeprefix("/api/v2")
        return httpx.Response(200, json={"dados": rotas[caminho], "links": []})

    return ClienteApi(URL_API_CAMARA, transport=httpx.MockTransport(handler), espera_inicial=0)


def test_buscar_votacoes_do_plenario_no_mes():
    recebidas = []

    with cliente_falso({"/votacoes": [votacao("1-1")]}, recebidas) as cliente:
        votacoes = buscar_votacoes(cliente, "2026-10")

    params = recebidas[0].url.params
    assert params["idOrgao"] == "180"
    assert params["dataInicio"] == "2026-10-01"
    assert params["dataFim"] == "2026-10-31"
    assert [v.id for v in votacoes] == ["1-1"]


def test_votacao_de_fora_do_mes_e_erro():
    dados = [votacao("1-1"), votacao("2-1", data="2026-11-03T15:00")]

    with cliente_falso({"/votacoes": dados}) as cliente, pytest.raises(IngestaoError, match="2-1"):
        buscar_votacoes(cliente, "2026-10")
