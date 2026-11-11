"""Ingestão das votações do Plenário no mês (ver ADR-008 e docs/spikes/s5-api-votacoes.md)."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pyarrow as pa

from monitor.ingestion.camara.modelos import ProposicaoApi, VotacaoApi, VotoApi
from monitor.ingestion.core.cliente import ClienteApi
from monitor.ingestion.core.erros import IngestaoError
from monitor.ingestion.core.parquet import gravar_tabela
from monitor.periodos import limites_do_mes

ID_PLENARIO = 180

ESQUEMA_VOTACOES = pa.schema(
    [
        ("id", pa.string()),
        ("data_hora_registro", pa.timestamp("us")),
        ("sigla_orgao", pa.string()),
        ("descricao", pa.string()),
        ("aprovacao", pa.bool_()),
        ("proposicao_objeto", pa.string()),
        ("nominal", pa.bool_()),
        ("_carregado_em", pa.timestamp("us", tz="UTC")),
    ]
)

ESQUEMA_VOTOS = pa.schema(
    [
        ("id_votacao", pa.string()),
        ("id_deputado", pa.int64()),
        ("nome", pa.string()),
        ("sigla_partido", pa.string()),
        ("sigla_uf", pa.string()),
        ("tipo_voto", pa.string()),
        ("data_registro_voto", pa.timestamp("us")),
        ("_carregado_em", pa.timestamp("us", tz="UTC")),
    ]
)

ESQUEMA_AFETADAS = pa.schema(
    [
        ("id_votacao", pa.string()),
        ("id_proposicao", pa.int64()),
        ("sigla_tipo", pa.string()),
        ("numero", pa.int32()),
        ("ano", pa.int32()),
        ("ementa", pa.string()),
        ("_carregado_em", pa.timestamp("us", tz="UTC")),
    ]
)


def buscar_votacoes(cliente: ClienteApi, mes: str) -> list[VotacaoApi]:
    """Votações do Plenário no mês. Falha se vierem votações de outras datas."""
    inicio, fim = limites_do_mes(mes)
    params = {
        "idOrgao": ID_PLENARIO,
        "dataInicio": inicio.isoformat(),
        "dataFim": fim.isoformat(),
        "ordem": "ASC",
        "ordenarPor": "dataHoraRegistro",
        "itens": 100,
    }
    votacoes = [VotacaoApi.model_validate(item) for item in cliente.paginar("/votacoes", params)]
    fora_do_mes = [v.id for v in votacoes if not inicio <= v.data_hora_registro.date() <= fim]
    if fora_do_mes:
        raise IngestaoError(
            f"Pedido para {mes}, mas vieram votações de outras datas: {fora_do_mes}."
        )
    return votacoes


def buscar_votos(cliente: ClienteApi, votacoes: list[VotacaoApi]) -> dict[str, list[VotoApi]]:
    """Os votos de cada votação. Uma lista vazia indica que não há votos registrados."""
    return {votacao.id: _votos_da_votacao(cliente, votacao.id) for votacao in votacoes}


def _votos_da_votacao(cliente: ClienteApi, id_votacao: str) -> list[VotoApi]:
    """Uma votação sem lista de votos (404) é tratada como sem votos registrados (ADR-008)."""
    try:
        dados = cliente.get_json(f"/votacoes/{id_votacao}/votos")["dados"]
    except httpx.HTTPStatusError as erro:
        if erro.response.status_code == 404:
            return []
        raise
    return [VotoApi.model_validate(item) for item in dados]


def buscar_proposicoes_afetadas(
    cliente: ClienteApi, ids_votacoes: list[str]
) -> list[tuple[str, ProposicaoApi]]:
    """As proposições afetadas por cada votação, como pares (id da votação, proposição)."""
    afetadas = []
    for id_votacao in ids_votacoes:
        detalhe = cliente.get_json(f"/votacoes/{id_votacao}")["dados"]
        afetadas.extend(
            (id_votacao, ProposicaoApi.model_validate(item))
            for item in detalhe.get("proposicoesAfetadas", [])
        )
    return afetadas


def gravar_votacoes(
    votacoes: list[VotacaoApi], votos: dict[str, list[VotoApi]], destino: Path
) -> Path:
    """Grava as votações, marcando como nominais as que têm votos registrados."""
    carregado_em = datetime.now(UTC)
    linhas = [
        {**v.model_dump(), "nominal": bool(votos.get(v.id)), "_carregado_em": carregado_em}
        for v in votacoes
    ]
    return gravar_tabela(linhas, ESQUEMA_VOTACOES, destino)


def gravar_votos(votos: dict[str, list[VotoApi]], destino: Path) -> Path:
    """Grava os votos de todas as votações: uma linha por votação e deputado."""
    carregado_em = datetime.now(UTC)
    linhas = [
        {
            "id_votacao": id_votacao,
            "id_deputado": voto.deputado.id,
            "nome": voto.deputado.nome,
            "sigla_partido": voto.deputado.sigla_partido,
            "sigla_uf": voto.deputado.sigla_uf,
            "tipo_voto": voto.tipo_voto,
            "data_registro_voto": voto.data_registro_voto,
            "_carregado_em": carregado_em,
        }
        for id_votacao, votos_da_votacao in votos.items()
        for voto in votos_da_votacao
    ]
    return gravar_tabela(linhas, ESQUEMA_VOTOS, destino)


def gravar_proposicoes_afetadas(afetadas: list[tuple[str, ProposicaoApi]], destino: Path) -> Path:
    """Grava as proposições afetadas: uma linha por votação e proposição."""
    carregado_em = datetime.now(UTC)
    linhas = [
        {
            "id_votacao": id_votacao,
            "id_proposicao": p.id,
            "sigla_tipo": p.sigla_tipo,
            "numero": p.numero,
            "ano": p.ano,
            "ementa": p.ementa,
            "_carregado_em": carregado_em,
        }
        for id_votacao, p in afetadas
    ]
    return gravar_tabela(linhas, ESQUEMA_AFETADAS, destino)


def ingerir_votacoes(cliente: ClienteApi, mes: str, pasta: Path) -> list[Path]:
    """Busca as votações do mês, os votos e as proposições afetadas das nominais."""
    votacoes = buscar_votacoes(cliente, mes)
    votos = buscar_votos(cliente, votacoes)
    nominais = [id_votacao for id_votacao, lista in votos.items() if lista]
    afetadas = buscar_proposicoes_afetadas(cliente, nominais)
    return [
        gravar_votacoes(votacoes, votos, pasta / f"votacoes_{mes}.parquet"),
        gravar_votos(votos, pasta / f"votos_{mes}.parquet"),
        gravar_proposicoes_afetadas(afetadas, pasta / f"afetadas_{mes}.parquet"),
    ]
