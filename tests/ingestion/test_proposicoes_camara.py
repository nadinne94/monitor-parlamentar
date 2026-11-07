from datetime import date

import httpx
import pytest

from monitor.ingestion.camara.deputados import URL_API_CAMARA
from monitor.ingestion.camara.modelos import ProposicaoApi
from monitor.ingestion.camara.proposicoes import buscar_autores, buscar_proposicoes, limites_do_mes
from monitor.ingestion.core.cliente import ClienteApi
from monitor.ingestion.core.erros import IngestaoError


@pytest.mark.parametrize(
    ("mes", "esperado"),
    [
        ("2026-10", (date(2026, 10, 1), date(2026, 10, 31))),
        ("2026-11", (date(2026, 11, 1), date(2026, 11, 30))),
        ("2028-02", (date(2028, 2, 1), date(2028, 2, 29))),
    ],
)
def test_limites_do_mes(mes, esperado):
    assert limites_do_mes(mes) == esperado


def proposicao(id_, sigla="PL", data="2026-10-20T16:12"):
    return {
        "id": id_,
        "siglaTipo": sigla,
        "codTipo": 139,
        "numero": id_,
        "ano": 2026,
        "ementa": f"Ementa {id_}",
        "dataApresentacao": data,
    }


def cliente_falso(rotas, recebidas=None):
    """Cliente que responde a cada caminho com os dados da rota correspondente."""

    def handler(request):
        if recebidas is not None:
            recebidas.append(request)
        caminho = request.url.path.removeprefix("/api/v2")
        return httpx.Response(200, json={"dados": rotas[caminho], "links": []})

    return ClienteApi(URL_API_CAMARA, transport=httpx.MockTransport(handler), espera_inicial=0)


def test_buscar_proposicoes_envia_os_filtros_do_mes():
    recebidas = []

    with cliente_falso({"/proposicoes": [proposicao(1)]}, recebidas) as cliente:
        proposicoes = buscar_proposicoes(cliente, "MG", "2026-10")

    params = recebidas[0].url.params
    assert params["siglaUfAutor"] == "MG"
    assert params["dataApresentacaoInicio"] == "2026-10-01"
    assert params["dataApresentacaoFim"] == "2026-10-31"
    assert params["itens"] == "100"
    assert [p.id for p in proposicoes] == [1]
    assert isinstance(proposicoes[0], ProposicaoApi)


def test_mes_sem_proposicoes_nao_e_erro():
    with cliente_falso({"/proposicoes": []}) as cliente:
        assert buscar_proposicoes(cliente, "MG", "2026-10") == []


def test_proposicao_de_fora_do_mes_e_erro():
    dados = [proposicao(1), proposicao(2, data="2026-09-30T10:00")]

    with cliente_falso({"/proposicoes": dados}) as cliente, pytest.raises(IngestaoError, match="2"):
        buscar_proposicoes(cliente, "MG", "2026-10")


def autor(id_deputado, nome, ordem=1):
    return {
        "uri": f"{URL_API_CAMARA}/deputados/{id_deputado}",
        "nome": nome,
        "codTipo": 10000,
        "tipo": "Deputado(a)",
        "ordemAssinatura": ordem,
        "proponente": 1,
    }


def test_buscar_autores_de_cada_proposicao():
    rotas = {
        "/proposicoes/1/autores": [autor(10, "Ana")],
        "/proposicoes/2/autores": [autor(10, "Ana"), autor(20, "Bruno", ordem=2)],
    }
    proposicoes = [ProposicaoApi.model_validate(proposicao(i)) for i in (1, 2)]

    with cliente_falso(rotas) as cliente:
        autores = buscar_autores(cliente, proposicoes)

    assert [(id_proposicao, a.nome) for id_proposicao, a in autores] == [
        (1, "Ana"),
        (2, "Ana"),
        (2, "Bruno"),
    ]
