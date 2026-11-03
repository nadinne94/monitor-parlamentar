"""Registro das ingestões disponíveis, por nome de fonte do sources.yaml (ver ADR-003)."""

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from monitor.ingestion.camara.deputados import ingerir_deputados
from monitor.ingestion.core.erros import ConfiguracaoError

Ingestor = Callable[[Mapping[str, Any], Path], list[Path]]


def ingerir_camara_api(parametros: Mapping[str, Any], dir_bruto: Path) -> list[Path]:
    uf = parametros.get("uf")
    if not uf:
        raise ConfiguracaoError("A fonte camara_api precisa do parâmetro 'uf' no sources.yaml.")
    destino = dir_bruto / "camara_api" / "deputados.parquet"
    return [ingerir_deputados(uf, destino)]


INGESTORES: dict[str, Ingestor] = {"camara_api": ingerir_camara_api}
