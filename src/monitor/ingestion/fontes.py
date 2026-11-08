"""Registro das ingestões disponíveis, por nome de fonte do sources.yaml (ver ADR-003)."""

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from monitor.ingestion.camara.deputados import URL_API_CAMARA, ingerir_deputados
from monitor.ingestion.camara.proposicoes import ingerir_proposicoes
from monitor.ingestion.core.cliente import ClienteApi
from monitor.ingestion.core.erros import ConfiguracaoError

Ingestor = Callable[[Mapping[str, Any], Path, list[str]], list[Path]]


def ingerir_camara_api(
    parametros: Mapping[str, Any], dir_bruto: Path, meses: list[str]
) -> list[Path]:
    uf = parametros.get("uf")
    if not uf:
        raise ConfiguracaoError("A fonte camara_api precisa do parâmetro 'uf' no sources.yaml.")
    pasta = dir_bruto / "camara_api"
    arquivos = [ingerir_deputados(uf, pasta / "deputados.parquet")]
    with ClienteApi(URL_API_CAMARA) as cliente:
        for mes in meses:
            arquivos.extend(ingerir_proposicoes(cliente, uf, mes, pasta))
    return arquivos


INGESTORES: dict[str, Ingestor] = {"camara_api": ingerir_camara_api}

# Tabelas que cada fonte grava, para recuperar a última coleta guardada (ADR-006).
# As fixas têm um arquivo só; as mensais, um arquivo por mês (ex.: proposicoes_2026-10).
TABELAS_FIXAS: dict[str, list[str]] = {"camara_api": ["deputados"]}
TABELAS_MENSAIS: dict[str, list[str]] = {"camara_api": ["proposicoes", "autores"]}


def tabelas_da_fonte(fonte: str, meses: list[str]) -> list[str]:
    """Os nomes das tabelas que a fonte grava para os meses dados, na ordem da ingestão."""
    mensais = [f"{tabela}_{mes}" for mes in meses for tabela in TABELAS_MENSAIS.get(fonte, [])]
    return TABELAS_FIXAS[fonte] + mensais
