from datetime import datetime

import duckdb
import httpx
import pytest

from monitor.ingestion.camara.deputados import URL_API_CAMARA
from monitor.ingestion.camara.modelos import ProposicaoApi, VotacaoApi, VotoApi
from monitor.ingestion.camara.votacoes import (
    buscar_proposicoes_afetadas,
    buscar_votacoes,
    buscar_votos,
    gravar_proposicoes_afetadas,
    gravar_votacoes,
    gravar_votos,
    ingerir_votacoes,
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
    """Cliente que responde a cada caminho com os dados da rota correspondente.

    Um caminho fora das rotas responde 404; uma rota com um número inteiro responde esse status.
    """

    def handler(request):
        if recebidas is not None:
            recebidas.append(request)
        caminho = request.url.path.removeprefix("/api/v2")
        resposta = rotas.get(caminho, 404)
        if isinstance(resposta, int):
            return httpx.Response(resposta)
        return httpx.Response(200, json={"dados": resposta, "links": []})

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


def test_gravar_votacoes_marca_as_nominais(tmp_path):
    votacoes = [VotacaoApi.model_validate(votacao(i)) for i in ("1-1", "2-1")]
    votos = {"1-1": [VotoApi.model_validate(voto(10))], "2-1": []}

    destino = gravar_votacoes(votacoes, votos, tmp_path / "votacoes.parquet")

    linhas = duckdb.sql(f"select id, nominal, aprovacao from '{destino}' order by id").fetchall()
    assert linhas == [("1-1", True, True), ("2-1", False, True)]


def test_gravar_votos_uma_linha_por_votacao_e_deputado(tmp_path):
    votos = {
        "1-1": [VotoApi.model_validate(voto(10)), VotoApi.model_validate(voto(20, "Não", "SP"))],
        "2-1": [],
    }

    destino = gravar_votos(votos, tmp_path / "votos.parquet")

    linhas = duckdb.sql(
        f"select id_votacao, id_deputado, sigla_uf, tipo_voto, data_registro_voto"
        f" from '{destino}' order by id_deputado"
    ).fetchall()
    assert linhas == [
        ("1-1", 10, "MG", "Sim", datetime(2026, 10, 14, 20, 31, 15)),
        ("1-1", 20, "SP", "Não", datetime(2026, 10, 14, 20, 31, 15)),
    ]


def test_gravar_proposicoes_afetadas(tmp_path):
    afetadas = [("1-1", ProposicaoApi.model_validate(proposicao(5)))]

    destino = gravar_proposicoes_afetadas(afetadas, tmp_path / "afetadas.parquet")

    linhas = duckdb.sql(f"select id_votacao, id_proposicao, sigla_tipo from '{destino}'").fetchall()
    assert linhas == [("1-1", 5, "PL")]


def test_ingerir_votacoes_busca_o_detalhe_so_das_nominais(tmp_path):
    recebidas = []
    rotas = {
        "/votacoes": [votacao("1-1"), votacao("2-1")],
        "/votacoes/1-1/votos": [voto(10)],
        "/votacoes/2-1/votos": [],
        "/votacoes/1-1": {"id": "1-1", "proposicoesAfetadas": [proposicao(5)]},
    }

    with cliente_falso(rotas, recebidas) as cliente:
        arquivos = ingerir_votacoes(cliente, "2026-10", tmp_path)

    assert [a.name for a in arquivos] == [
        "votacoes_2026-10.parquet",
        "votos_2026-10.parquet",
        "afetadas_2026-10.parquet",
    ]
    assert "/api/v2/votacoes/2-1" not in [r.url.path for r in recebidas]


def test_votacao_sem_lista_de_votos_e_tratada_como_sem_votos():
    votacoes = [VotacaoApi.model_validate(votacao("1-1"))]

    with cliente_falso({}) as cliente:
        assert buscar_votos(cliente, votacoes) == {"1-1": []}


def test_outros_erros_na_lista_de_votos_continuam_sendo_erros():
    votacoes = [VotacaoApi.model_validate(votacao("1-1"))]

    with (
        cliente_falso({"/votacoes/1-1/votos": 400}) as cliente,
        pytest.raises(httpx.HTTPStatusError),
    ):
        buscar_votos(cliente, votacoes)


def test_gravar_votacoes_guarda_o_link_do_evento(tmp_path):
    com_evento = {
        **votacao("1-1"),
        "uriEvento": "https://dadosabertos.camara.leg.br/api/v2/eventos/1",
    }
    votacoes = [VotacaoApi.model_validate(com_evento), VotacaoApi.model_validate(votacao("2-1"))]

    destino = gravar_votacoes(votacoes, {}, tmp_path / "votacoes.parquet")

    linhas = duckdb.sql(f"select id, uri_evento is null from '{destino}' order by id").fetchall()
    assert linhas == [("1-1", False), ("2-1", True)]
