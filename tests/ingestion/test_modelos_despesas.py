from datetime import datetime
from decimal import Decimal

import pytest

from monitor.ingestion.camara.modelos import DespesaApi


@pytest.fixture
def item_despesa():
    """Um item no formato real de `/deputados/{id}/despesas` (docs/spikes/s6-api-despesas.md).

    Os valores são os de uma despesa real; o fornecedor e o documento dele são fictícios.
    """
    return {
        "ano": 2026,
        "mes": 10,
        "tipoDespesa": "DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR.",
        "codDocumento": "8166223",
        "tipoDocumento": "Nota Fiscal",
        "codTipoDocumento": 0,
        "dataDocumento": "2026-10-01T00:00:00",
        "numDocumento": "23073",
        "valorDocumento": 266.65,
        "urlDocumento": (
            "https://www.camara.leg.br/cota-parlamentar/documentos/publ/233/2026/8166223.pdf"
        ),
        "nomeFornecedor": "GRAFICA EXEMPLO LTDA",
        "cnpjCpfFornecedor": "12345678000199",
        "valorLiquido": -266.65,
        "valorGlosa": 0.0,
        "numRessarcimento": "",
        "codLote": 2270923,
        "parcela": 0,
    }


def test_converte_despesa_com_cnpj(item_despesa):
    despesa = DespesaApi.model_validate(item_despesa)

    assert despesa.ano == 2026
    assert despesa.mes == 10
    assert despesa.tipo_despesa == "DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR."
    assert despesa.cod_documento == "8166223"
    assert despesa.data_documento == datetime(2026, 10, 1)
    assert despesa.valor_documento == Decimal("266.65")
    assert despesa.valor_liquido == Decimal("-266.65")
    assert despesa.documento_fornecedor == "12345678000199"
    assert despesa.nome_fornecedor == "GRAFICA EXEMPLO LTDA"
    assert despesa.fornecedor_pessoa_fisica is False


def test_fornecedor_pessoa_fisica_sai_protegido(item_despesa):
    item_despesa["cnpjCpfFornecedor"] = "12345678901"
    item_despesa["nomeFornecedor"] = "JOAO DA SILVA"

    despesa = DespesaApi.model_validate(item_despesa)

    assert despesa.fornecedor_pessoa_fisica is True
    assert despesa.documento_fornecedor == "***.456.789-**"
    assert despesa.nome_fornecedor is None
    assert despesa.url_documento is None
    assert "12345678901" not in despesa.model_dump_json()


def test_cpf_no_nome_de_empresa_e_mascarado(item_despesa):
    item_despesa["nomeFornecedor"] = "JOAO DA SILVA 12345678901"

    despesa = DespesaApi.model_validate(item_despesa)

    assert despesa.nome_fornecedor == "JOAO DA SILVA ***.456.789-**"
    assert despesa.fornecedor_pessoa_fisica is False
