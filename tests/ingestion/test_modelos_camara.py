import pytest

from monitor.ingestion.camara.modelos import DeputadoApi


@pytest.fixture
def item_api():
    """Um item real da lista de deputados (ver docs/spikes/s0-api-deputados.md)."""
    return {
        "id": 74646,
        "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/74646",
        "nome": "Aécio Neves",
        "siglaPartido": "PSDB",
        "uriPartido": "https://dadosabertos.camara.leg.br/api/v2/partidos/36835",
        "siglaUf": "MG",
        "idLegislatura": 57,
        "urlFoto": "https://www.camara.leg.br/internet/deputado/bandep/74646.jpg",
        "email": "dep.aecioneves@camara.leg.br",
    }


def test_converte_item_da_api(item_api):
    deputado = DeputadoApi.model_validate(item_api)

    assert deputado.id == 74646
    assert deputado.nome == "Aécio Neves"
    assert deputado.sigla_partido == "PSDB"
    assert deputado.sigla_uf == "MG"
    assert deputado.id_legislatura == 57
    assert deputado.url_foto == "https://www.camara.leg.br/internet/deputado/bandep/74646.jpg"
    assert deputado.email == "dep.aecioneves@camara.leg.br"
