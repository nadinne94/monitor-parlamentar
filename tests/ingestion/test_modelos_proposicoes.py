from datetime import datetime

import pytest

from monitor.ingestion.camara.modelos import ProposicaoApi


@pytest.fixture
def item_proposicao():
    """Um item real da lista de proposições (ver docs/spikes/s3-api-proposicoes.md)."""
    return {
        "id": 2648590,
        "uri": "https://dadosabertos.camara.leg.br/api/v2/proposicoes/2648590",
        "siglaTipo": "PL",
        "codTipo": 139,
        "numero": 5620,
        "ano": 2026,
        "ementa": "Institui o sistema eleitoral distrital misto nas eleições para a Câmara.",
        "dataApresentacao": "2026-10-20T16:12",
    }


def test_converte_item_da_lista(item_proposicao):
    proposicao = ProposicaoApi.model_validate(item_proposicao)

    assert proposicao.id == 2648590
    assert proposicao.sigla_tipo == "PL"
    assert proposicao.cod_tipo == 139
    assert (proposicao.numero, proposicao.ano) == (5620, 2026)
    assert proposicao.data_apresentacao == datetime(2026, 10, 20, 16, 12)
