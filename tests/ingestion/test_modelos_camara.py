import pytest
from pydantic import ValidationError

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


def test_campos_nao_essenciais_sao_opcionais(item_api):
    item_api["email"] = None
    del item_api["urlFoto"]
    del item_api["siglaPartido"]

    deputado = DeputadoApi.model_validate(item_api)

    assert deputado.email is None
    assert deputado.url_foto is None
    assert deputado.sigla_partido is None


def test_campos_desconhecidos_sao_descartados(item_api):
    item_api["cpf"] = "00000000000"

    deputado = DeputadoApi.model_validate(item_api)

    assert "cpf" not in deputado.model_dump()
    assert "uri" not in deputado.model_dump()


def test_deputado_e_imutavel(item_api):
    deputado = DeputadoApi.model_validate(item_api)

    with pytest.raises(ValidationError):
        deputado.nome = "Outro nome"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("id", None),
        ("id", "abc"),
        ("nome", ""),
        ("siglaUf", "Minas"),
        ("idLegislatura", 0),
    ],
)
def test_rejeita_campo_essencial_invalido(item_api, campo, valor):
    item_api[campo] = valor

    with pytest.raises(ValidationError):
        DeputadoApi.model_validate(item_api)


def test_remove_espacos_nas_pontas(item_api):
    item_api["nome"] = "  Aécio Neves  "

    deputado = DeputadoApi.model_validate(item_api)

    assert deputado.nome == "Aécio Neves"
