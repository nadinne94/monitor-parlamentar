"""Ingestão das despesas da cota parlamentar (ver ADR-009 e docs/spikes/s6-api-despesas.md)."""

from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa

from monitor.ingestion.camara.deputados import buscar_deputados
from monitor.ingestion.camara.modelos import DespesaApi
from monitor.ingestion.core.cliente import ClienteApi
from monitor.ingestion.core.erros import IngestaoError
from monitor.ingestion.core.parquet import gravar_tabela

# Valores em reais, com duas casas: o tipo decimal guarda o valor exato, sem arredondamento.
DINHEIRO = pa.decimal128(12, 2)

ESQUEMA_DESPESAS = pa.schema(
    [
        ("id_deputado", pa.int64()),
        ("ano", pa.int32()),
        ("mes", pa.int32()),
        ("tipo_despesa", pa.string()),
        ("cod_documento", pa.string()),
        ("tipo_documento", pa.string()),
        ("data_documento", pa.timestamp("us")),
        ("num_documento", pa.string()),
        ("valor_documento", DINHEIRO),
        ("valor_glosa", DINHEIRO),
        ("valor_liquido", DINHEIRO),
        ("url_documento", pa.string()),
        ("nome_fornecedor", pa.string()),
        ("documento_fornecedor", pa.string()),
        ("fornecedor_pessoa_fisica", pa.bool_()),
        ("parcela", pa.int32()),
        ("_carregado_em", pa.timestamp("us", tz="UTC")),
    ]
)


def buscar_despesas(cliente: ClienteApi, id_deputado: int, mes: str) -> list[DespesaApi]:
    """Despesas do deputado na competência (AAAA-MM).

    Sempre com ano e mês: sem eles, a API aplica um recorte padrão de cerca de seis meses
    (ADR-009, seção 2).
    """
    ano, numero = (int(parte) for parte in mes.split("-"))
    params = {
        "ano": ano,
        "mes": numero,
        "ordem": "ASC",
        "ordenarPor": "dataDocumento",
        "itens": 100,
    }
    caminho = f"/deputados/{id_deputado}/despesas"
    despesas = [DespesaApi.model_validate(item) for item in cliente.paginar(caminho, params)]
    outras = sorted({f"{d.ano}-{d.mes:02d}" for d in despesas} - {mes})
    if outras:
        raise IngestaoError(
            f"Pedido para {mes}, mas vieram despesas das competências: {', '.join(outras)}."
        )
    return despesas


def gravar_despesas(despesas: dict[int, list[DespesaApi]], destino: Path) -> Path:
    """Grava as despesas de todos os deputados: uma linha por lançamento."""
    carregado_em = datetime.now(UTC)
    linhas = [
        {"id_deputado": id_deputado, **d.model_dump(), "_carregado_em": carregado_em}
        for id_deputado, lista in despesas.items()
        for d in lista
    ]
    return gravar_tabela(linhas, ESQUEMA_DESPESAS, destino)


def ingerir_despesas(cliente: ClienteApi, uf: str, mes: str, pasta: Path) -> list[Path]:
    """Busca as despesas de cada deputado da UF na competência e grava um Parquet do mês."""
    despesas = {d.id: buscar_despesas(cliente, d.id, mes) for d in buscar_deputados(cliente, uf)}
    return [gravar_despesas(despesas, pasta / f"despesas_{mes}.parquet")]
