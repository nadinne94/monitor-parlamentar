"""Armazenamento dos dados brutos numa release do GitHub (ADR-006)."""

import shutil
import subprocess
import tempfile
from collections.abc import Callable
from datetime import date
from pathlib import Path

REPOSITORIO = "nadinne94/monitor-parlamentar"
RELEASE = "dados-brutos"


def nome_no_armazenamento(fonte: str, tabela: str, dia: date | None = None) -> str:
    """camara_api + deputados -> camara_api__deputados.parquet (com __AAAA-MM-DD se houver dia)."""
    sufixo = f"__{dia.isoformat()}" if dia else ""
    return f"{fonte}__{tabela}{sufixo}.parquet"


def guardar(
    fonte: str,
    arquivos: list[Path],
    dia: date,
    executar: Callable[..., object] = subprocess.run,
) -> list[str]:
    """Envia cada arquivo para a release duas vezes: como "mais recente" e como cópia do dia."""
    nomes = []
    with tempfile.TemporaryDirectory() as pasta:
        copias = []
        for arquivo in arquivos:
            for nome in (
                nome_no_armazenamento(fonte, arquivo.stem),
                nome_no_armazenamento(fonte, arquivo.stem, dia),
            ):
                copia = Path(pasta) / nome
                shutil.copyfile(arquivo, copia)
                copias.append(str(copia))
                nomes.append(nome)
        comando = ["gh", "release", "upload", RELEASE, *copias, "--clobber", "--repo", REPOSITORIO]
        executar(comando, check=True)
    return nomes
