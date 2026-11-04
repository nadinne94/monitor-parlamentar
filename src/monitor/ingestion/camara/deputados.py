"""Ingestão da lista de deputados da API da Câmara (ver docs/spikes/s0-api-deputados.md)."""

from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from monitor.ingestion.camara.modelos import DeputadoApi
from monitor.ingestion.core.cliente import ClienteApi
from monitor.ingestion.core.erros import IngestaoError

URL_API_CAMARA = "https://dadosabertos.camara.leg.br/api/v2"

ESQUEMA_DEPUTADOS = pa.schema(
    [
        ("id", pa.int64()),
        ("nome", pa.string()),
        ("sigla_uf", pa.string()),
        ("id_legislatura", pa.int64()),
        ("sigla_partido", pa.string()),
        ("url_foto", pa.string()),
        ("email", pa.string()),
        ("_carregado_em", pa.timestamp("us", tz="UTC")),
    ]
)


def buscar_deputados(cliente: ClienteApi, uf: str) -> list[DeputadoApi]:
    """Deputados em exercício da UF, validados. Falha se a lista vier vazia ou com outra UF."""
    params = {"siglaUf": uf, "ordem": "ASC", "ordenarPor": "nome", "itens": 100}
    deputados = [DeputadoApi.model_validate(item) for item in cliente.paginar("/deputados", params)]

    if not deputados:
        raise IngestaoError(f"A API não devolveu nenhum deputado para a UF {uf}.")
    outras_ufs = sorted({d.sigla_uf for d in deputados if d.sigla_uf != uf})
    if outras_ufs:
        raise IngestaoError(f"Pedido para {uf}, mas vieram deputados de: {', '.join(outras_ufs)}.")
    return deputados


def gravar_parquet(deputados: list[DeputadoApi], destino: Path) -> Path:
    """Grava os deputados em Parquet, com o horário da carga."""
    carregado_em = datetime.now(UTC)
    linhas = [{**d.model_dump(), "_carregado_em": carregado_em} for d in deputados]
    tabela = pa.Table.from_pylist(linhas, schema=ESQUEMA_DEPUTADOS)
    destino.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(tabela, destino)
    return destino


def ingerir_deputados(uf: str, destino: Path) -> Path:
    """Busca os deputados da UF na API da Câmara e grava o Parquet bruto."""
    with ClienteApi(URL_API_CAMARA) as cliente:
        deputados = buscar_deputados(cliente, uf)
    return gravar_parquet(deputados, destino)
