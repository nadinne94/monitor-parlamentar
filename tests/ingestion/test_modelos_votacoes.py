from datetime import datetime

import pytest
from pydantic import ValidationError

from monitor.ingestion.camara.modelos import VotacaoApi, VotoApi


@pytest.fixture
def item_votacao():
    """Um item real da lista de votações (ver docs/spikes/s5-api-votacoes.md)."""
    return {
        "id": "2236186-60",
        "uri": "https://dadosabertos.camara.leg.br/api/v2/votacoes/2236186-60",
        "data": "2026-10-14",
        "dataHoraRegistro": "2026-10-14T20:56:14",
        "siglaOrgao": "PLEN",
        "descricao": "Rejeitada a Subemenda Substitutiva ao Projeto de Lei Complementar nº 281, "
        "de 2019. Sim: 252; Não: 176; Total: 428.",
        "aprovacao": 0,
    }


def test_converte_item_da_lista(item_votacao):
    votacao = VotacaoApi.model_validate(item_votacao)

    assert votacao.id == "2236186-60"
    assert votacao.data_hora_registro == datetime(2026, 10, 14, 20, 56, 14)
    assert votacao.sigla_orgao == "PLEN"
    assert votacao.aprovacao is False
    assert votacao.proposicao_objeto is None


def test_votacao_sem_aprovacao(item_votacao):
    del item_votacao["aprovacao"]
    item_votacao["descricao"] = "Mantido o texto."

    assert VotacaoApi.model_validate(item_votacao).aprovacao is None


@pytest.mark.parametrize("id_invalido", ["", "2236186", "abc-60"])
def test_rejeita_id_fora_do_formato(item_votacao, id_invalido):
    item_votacao["id"] = id_invalido

    with pytest.raises(ValidationError):
        VotacaoApi.model_validate(item_votacao)


@pytest.fixture
def item_voto():
    """Um item real da lista de votos (ver docs/spikes/s5-api-votacoes.md)."""
    return {
        "tipoVoto": "Sim",
        "dataRegistroVoto": "2026-10-14T20:31:15",
        "deputado_": {
            "id": 209787,
            "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/209787",
            "nome": "Nikolas Ferreira",
            "siglaPartido": "PL",
            "siglaUf": "MG",
            "idLegislatura": 57,
        },
    }


def test_converte_voto_com_o_deputado(item_voto):
    voto = VotoApi.model_validate(item_voto)

    assert voto.tipo_voto == "Sim"
    assert voto.deputado.id == 209787
    assert voto.deputado.sigla_uf == "MG"


def test_voto_artigo_17_e_aceito(item_voto):
    item_voto["tipoVoto"] = "Artigo 17"

    assert VotoApi.model_validate(item_voto).tipo_voto == "Artigo 17"


def test_rejeita_voto_sem_uf(item_voto):
    del item_voto["deputado_"]["siglaUf"]

    with pytest.raises(ValidationError):
        VotoApi.model_validate(item_voto)
