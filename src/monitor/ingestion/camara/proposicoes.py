"""Ingestão das proposições do mês (ver ADR-007 e docs/spikes/s3-api-proposicoes.md)."""

import calendar
from datetime import UTC, date, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from monitor.ingestion.camara.modelos import AutorApi, ProposicaoApi
from monitor.ingestion.core.cliente import ClienteApi
from monitor.ingestion.core.erros import IngestaoError

ESQUEMA_PROPOSICOES = pa.schema(
    [
        ("id", pa.int64()),
        ("sigla_tipo", pa.string()),
        ("cod_tipo", pa.int32()),
        ("numero", pa.int32()),
        ("ano", pa.int32()),
        ("ementa", pa.string()),
        ("data_apresentacao", pa.timestamp("us")),
        ("_carregado_em", pa.timestamp("us", tz="UTC")),
    ]
)

ESQUEMA_AUTORES = pa.schema(
    [
        ("id_proposicao", pa.int64()),
        ("id_deputado", pa.int64()),
        ("nome", pa.string()),
        ("tipo", pa.string()),
        ("cod_tipo", pa.int32()),
        ("ordem_assinatura", pa.int32()),
        ("proponente", pa.bool_()),
        ("_carregado_em", pa.timestamp("us", tz="UTC")),
    ]
)


def limites_do_mes(mes: str) -> tuple[date, date]:
    """'2026-10' -> (date(2026, 10, 1), date(2026, 10, 31))."""
    ano, numero = (int(parte) for parte in mes.split("-"))
    ultimo_dia = calendar.monthrange(ano, numero)[1]
    return date(ano, numero, 1), date(ano, numero, ultimo_dia)


def buscar_proposicoes(cliente: ClienteApi, uf: str, mes: str) -> list[ProposicaoApi]:
    """Proposições apresentadas no mês por deputados da UF."""
    inicio, fim = limites_do_mes(mes)
    params = {
        "siglaUfAutor": uf,
        "dataApresentacaoInicio": inicio.isoformat(),
        "dataApresentacaoFim": fim.isoformat(),
        "ordem": "ASC",
        "ordenarPor": "id",
        "itens": 100,
    }
    proposicoes = [
        ProposicaoApi.model_validate(item) for item in cliente.paginar("/proposicoes", params)
    ]
    fora_do_mes = [p.id for p in proposicoes if not inicio <= p.data_apresentacao.date() <= fim]
    if fora_do_mes:
        raise IngestaoError(
            f"Pedido para {mes}, mas vieram proposições de outras datas: {fora_do_mes}."
        )
    return proposicoes


def buscar_autores(
    cliente: ClienteApi, proposicoes: list[ProposicaoApi]
) -> list[tuple[int, AutorApi]]:
    """Os autores de cada proposição, como pares (id da proposição, autor)."""
    autores = []
    for proposicao in proposicoes:
        corpo = cliente.get_json(f"/proposicoes/{proposicao.id}/autores")
        autores.extend((proposicao.id, AutorApi.model_validate(item)) for item in corpo["dados"])
    return autores


def gravar_proposicoes(proposicoes: list[ProposicaoApi], destino: Path) -> Path:
    """Grava as proposições em Parquet, com esquema explícito e horário da carga."""
    carregado_em = datetime.now(UTC)
    linhas = [{**p.model_dump(), "_carregado_em": carregado_em} for p in proposicoes]
    return _gravar(linhas, ESQUEMA_PROPOSICOES, destino)


def gravar_autores(autores: list[tuple[int, AutorApi]], destino: Path) -> Path:
    """Grava os autores em Parquet: uma linha por proposição e autor."""
    carregado_em = datetime.now(UTC)
    linhas = [
        {
            **autor.model_dump(),
            "id_proposicao": id_proposicao,
            "id_deputado": autor.id_deputado,
            "_carregado_em": carregado_em,
        }
        for id_proposicao, autor in autores
    ]
    return _gravar(linhas, ESQUEMA_AUTORES, destino)


def _gravar(linhas: list[dict], esquema: pa.Schema, destino: Path) -> Path:
    tabela = pa.Table.from_pylist(linhas, schema=esquema)
    destino.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(tabela, destino)
    return destino


def ingerir_proposicoes(cliente: ClienteApi, uf: str, mes: str, pasta: Path) -> list[Path]:
    """Busca as proposições do mês e os seus autores, e grava os dois Parquets brutos."""
    proposicoes = buscar_proposicoes(cliente, uf, mes)
    autores = buscar_autores(cliente, proposicoes)
    return [
        gravar_proposicoes(proposicoes, pasta / f"proposicoes_{mes}.parquet"),
        gravar_autores(autores, pasta / f"autores_{mes}.parquet"),
    ]
