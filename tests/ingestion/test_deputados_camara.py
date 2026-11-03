import duckdb
import httpx
import pytest

from monitor.ingestion.camara.deputados import (
    URL_API_CAMARA,
    IngestaoError,
    buscar_deputados,
    gravar_parquet,
)
from monitor.ingestion.camara.modelos import DeputadoApi
from monitor.ingestion.core.cliente import ClienteApi


def deputado(id_, nome, uf="MG", **extra):
    return {"id": id_, "nome": nome, "siglaUf": uf, "idLegislatura": 57, **extra}


def cliente_com_dados(dados, recebidas=None):
    def handler(request):
        if recebidas is not None:
            recebidas.append(request)
        return httpx.Response(200, json={"dados": dados, "links": []})

    return ClienteApi(URL_API_CAMARA, transport=httpx.MockTransport(handler), espera_inicial=0)


def test_buscar_deputados_valida_cada_item():
    with cliente_com_dados([deputado(1, "Ana"), deputado(2, "Bruno")]) as cliente:
        deputados = buscar_deputados(cliente, "MG")

    assert [d.nome for d in deputados] == ["Ana", "Bruno"]
    assert all(isinstance(d, DeputadoApi) for d in deputados)


def test_buscar_deputados_envia_os_filtros():
    recebidas = []

    with cliente_com_dados([deputado(1, "Ana")], recebidas) as cliente:
        buscar_deputados(cliente, "MG")

    params = recebidas[0].url.params
    assert params["siglaUf"] == "MG"
    assert params["itens"] == "100"
    assert recebidas[0].url.path == "/api/v2/deputados"


def test_lista_vazia_e_erro():
    with cliente_com_dados([]) as cliente, pytest.raises(IngestaoError, match="nenhum deputado"):
        buscar_deputados(cliente, "MG")


def test_deputado_de_outra_uf_e_erro():
    dados = [deputado(1, "Ana"), deputado(2, "Carla", uf="SP")]

    with cliente_com_dados(dados) as cliente, pytest.raises(IngestaoError, match="SP"):
        buscar_deputados(cliente, "MG")


def test_gravar_parquet_preserva_dados_e_tipos(tmp_path):
    deputados = [
        DeputadoApi.model_validate(deputado(1, "Ana", siglaPartido="PT")),
        DeputadoApi.model_validate(deputado(2, "Bruno")),
    ]
    destino = tmp_path / "bruto" / "deputados.parquet"
    gravar_parquet(deputados, destino)
    with duckdb.connect() as conexao:
        linhas = conexao.execute(
            "select id, nome, sigla_partido, email from read_parquet(?) order by id",
            [str(destino)],
        ).fetchall()
        tipos = conexao.execute(
            "select typeof(id), typeof(email), typeof(_carregado_em) from read_parquet(?) limit 1",
            [str(destino)],
        ).fetchone()

    assert linhas == [(1, "Ana", "PT", None), (2, "Bruno", None, None)]
    assert tipos == ("BIGINT", "VARCHAR", "TIMESTAMP WITH TIME ZONE")
