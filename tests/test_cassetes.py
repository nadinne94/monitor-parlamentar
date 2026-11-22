import json

from monitor.ingestion.camara.modelos import DespesaApi
from tests.cassetes import anonimizar_despesas


def resposta(nome, documento, url="https://www.camara.leg.br/cota-parlamentar/documentos/1.pdf"):
    item = {
        "ano": 2026,
        "mes": 10,
        "tipoDespesa": "MANUTENÇÃO DE ESCRITÓRIO DE APOIO À ATIVIDADE PARLAMENTAR",
        "codDocumento": "1",
        "valorLiquido": -100.0,
        "nomeFornecedor": nome,
        "cnpjCpfFornecedor": documento,
        "urlDocumento": url,
    }
    return json.dumps({"dados": [item], "links": []})


def test_cpf_de_fornecedor_vira_um_cpf_ficticio_sem_nome_e_sem_comprovante():
    corpo = anonimizar_despesas(resposta("JOAO DA SILVA", "12345678901"))

    assert "12345678901" not in corpo
    assert "JOAO DA SILVA" not in corpo
    item = json.loads(corpo)["dados"][0]
    assert item["cnpjCpfFornecedor"] == "00000000000"
    assert item["urlDocumento"] is None
    assert DespesaApi.model_validate(item).fornecedor_pessoa_fisica is True


def test_empresa_mantem_o_cnpj_e_perde_o_cpf_do_nome():
    corpo = anonimizar_despesas(resposta("JOAO DA SILVA 12345678901", "12345678000199"))

    item = json.loads(corpo)["dados"][0]
    assert item["cnpjCpfFornecedor"] == "12345678000199"
    assert item["nomeFornecedor"] == "JOAO DA SILVA ***.456.789-**"
