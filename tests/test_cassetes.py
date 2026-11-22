import json

from monitor.ingestion.camara.modelos import DespesaApi
from tests.cassetes import anonimizar_despesas, preparar_resposta


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


def gravada(corpo: bytes, status: int = 200) -> dict:
    """Uma resposta no formato em que o vcrpy a entrega antes de gravar."""
    return {
        "status": {"code": status, "message": "OK"},
        "headers": {"Content-Length": [str(len(corpo))]},
        "body": {"string": corpo},
    }


def test_resposta_de_despesas_e_anonimizada_antes_de_gravar():
    original = resposta("JOAO DA SILVA", "12345678901").encode()

    preparada = preparar_resposta(gravada(original))

    corpo = preparada["body"]["string"]
    assert b"12345678901" not in corpo
    assert preparada["headers"]["Content-Length"] == [str(len(corpo))]


def test_outras_respostas_sao_gravadas_como_vieram():
    original = b'{"dados": [{"id": 74646, "nome": "Dep"}], "links": []}'

    assert preparar_resposta(gravada(original))["body"]["string"] == original


def test_erro_do_servidor_nao_e_gravado():
    assert preparar_resposta(gravada(b"", status=504)) is None
