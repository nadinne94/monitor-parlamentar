import httpx
import pytest

from monitor.ingestion.camara.deputados import URL_API_CAMARA
from monitor.ingestion.camara.modelos import VotacaoApi
from monitor.ingestion.camara.votacoes import (
    buscar_proposicoes_afetadas,
    buscar_votacoes,
    buscar_votos,
)
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


def voto(id_deputado, tipo="Sim", uf="MG"):
    return {
        "tipoVoto": tipo,
        "dataRegistroVoto": "2026-10-14T20:31:15",
        "deputado_": {"id": id_deputado, "nome": f"Dep {id_deputado}", "siglaUf": uf},
    }


def proposicao(id_, sigla="PL"):
    return {
        "id": id_,
        "siglaTipo": sigla,
        "codTipo": 139,
        "numero": id_,
        "ano": 2026,
        "ementa": f"Ementa {id_}",
        "dataApresentacao": "2026-03-25T08:24",
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


def test_buscar_votos_separa_nominais_de_simbolicas():
    rotas = {
        "/votacoes/1-1/votos": [voto(10), voto(20, "Não", "SP")],
        "/votacoes/2-1/votos": [],
    }
    votacoes = [VotacaoApi.model_validate(votacao(i)) for i in ("1-1", "2-1")]

    with cliente_falso(rotas) as cliente:
        votos = buscar_votos(cliente, votacoes)

    assert [v.deputado.id for v in votos["1-1"]] == [10, 20]
    assert votos["2-1"] == []


def test_buscar_proposicoes_afetadas():
    rotas = {"/votacoes/1-1": {"id": "1-1", "proposicoesAfetadas": [proposicao(5)]}}

    with cliente_falso(rotas) as cliente:
        afetadas = buscar_proposicoes_afetadas(cliente, ["1-1"])

    assert [(id_votacao, p.id) for id_votacao, p in afetadas] == [("1-1", 5)]


def test_votacao_sem_proposicoes_afetadas():
    with cliente_falso({"/votacoes/1-1": {"id": "1-1"}}) as cliente:
        assert buscar_proposicoes_afetadas(cliente, ["1-1"]) == []
