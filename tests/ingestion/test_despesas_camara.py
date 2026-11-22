from decimal import Decimal

import duckdb
import httpx
import pytest

from monitor.ingestion.camara.deputados import URL_API_CAMARA
from monitor.ingestion.camara.despesas import buscar_despesas, gravar_despesas
from monitor.ingestion.camara.modelos import DespesaApi
from monitor.ingestion.core.cliente import ClienteApi
from monitor.ingestion.core.erros import IngestaoError


def despesa(cod="8166223", mes=10, documento="12345678000199"):
    """Um item no formato de `/deputados/{id}/despesas`, com fornecedor fictício."""
    return {
        "ano": 2026,
        "mes": mes,
        "tipoDespesa": "COMBUSTÍVEIS E LUBRIFICANTES.",
        "codDocumento": cod,
        "dataDocumento": f"2026-{mes:02d}-05T00:00:00",
        "valorDocumento": 150.0,
        "valorGlosa": 0.0,
        "valorLiquido": -150.0,
        "nomeFornecedor": "POSTO EXEMPLO LTDA",
        "cnpjCpfFornecedor": documento,
    }


def cliente_falso(rotas, recebidas=None):
    """Cliente que responde a cada caminho com os dados da rota correspondente (404 fora delas)."""

    def handler(request):
        if recebidas is not None:
            recebidas.append(request)
        caminho = request.url.path.removeprefix("/api/v2")
        if caminho not in rotas:
            return httpx.Response(404)
        return httpx.Response(200, json={"dados": rotas[caminho], "links": []})

    return ClienteApi(URL_API_CAMARA, transport=httpx.MockTransport(handler), espera_inicial=0)


def test_busca_as_despesas_do_deputado_com_ano_e_mes():
    recebidas = []

    with cliente_falso({"/deputados/74646/despesas": [despesa()]}, recebidas) as cliente:
        despesas = buscar_despesas(cliente, 74646, "2026-10")

    params = recebidas[0].url.params
    assert params["ano"] == "2026"
    assert params["mes"] == "10"
    assert params["itens"] == "100"
    assert [d.cod_documento for d in despesas] == ["8166223"]


def test_falha_se_vier_despesa_de_outra_competencia():
    rotas = {"/deputados/74646/despesas": [despesa(), despesa(cod="2", mes=9)]}

    with cliente_falso(rotas) as cliente, pytest.raises(IngestaoError, match="2026-09"):
        buscar_despesas(cliente, 74646, "2026-10")


def test_grava_as_despesas_com_valores_em_decimal(tmp_path):
    despesas = {
        74646: [DespesaApi.model_validate(despesa())],
        204512: [DespesaApi.model_validate(despesa(cod="9", documento="12345678901"))],
    }

    destino = gravar_despesas(despesas, tmp_path / "despesas_2026-10.parquet")

    linhas = duckdb.sql(
        f"select id_deputado, valor_liquido, documento_fornecedor, typeof(valor_liquido) "
        f"from '{destino}' order by id_deputado"
    ).fetchall()
    assert linhas == [
        (74646, Decimal("-150.00"), "12345678000199", "DECIMAL(12,2)"),
        (204512, Decimal("-150.00"), "***.456.789-**", "DECIMAL(12,2)"),
    ]
