from datetime import datetime

import pytest
from pydantic import ValidationError

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


def test_documento_acessorio_tem_ano_zero(item_proposicao):
    item_proposicao.update(siglaTipo="PRL", codTipo=190, numero=1, ano=0)

    proposicao = ProposicaoApi.model_validate(item_proposicao)

    assert proposicao.ano == 0


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("id", 0), ("siglaTipo", ""), ("dataApresentacao", "ontem"), ("ano", -1)],
)
def test_rejeita_proposicao_invalida(item_proposicao, campo, valor):
    item_proposicao[campo] = valor

    with pytest.raises(ValidationError):
        ProposicaoApi.model_validate(item_proposicao)
