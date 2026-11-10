"""Gravação dos Parquets brutos, com esquema explícito."""

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def gravar_tabela(linhas: list[dict], esquema: pa.Schema, destino: Path) -> Path:
    """Grava as linhas em Parquet com o esquema dado, criando a pasta se preciso."""
    tabela = pa.Table.from_pylist(linhas, schema=esquema)
    destino.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(tabela, destino)
    return destino
