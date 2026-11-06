"""Armazenamento dos dados brutos numa release do GitHub (ADR-006)."""

import shutil
import subprocess
import tempfile
from collections.abc import Callable
from datetime import date
from pathlib import Path

import httpx

from monitor.ingestion.core.cliente import USER_AGENT

REPOSITORIO = "nadinne94/monitor-parlamentar"
RELEASE = "dados-brutos"


class ArmazenamentoError(Exception):
    """Não foi possível guardar ou recuperar os dados brutos."""


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
        try:
            executar(comando, check=True)
        except subprocess.CalledProcessError as erro:
            raise ArmazenamentoError(
                f"Falha ao enviar os dados de {fonte} para a release."
            ) from erro
    return nomes


def recuperar(
    fonte: str,
    tabelas: list[str],
    dir_bruto: Path,
    transport: httpx.BaseTransport | None = None,
) -> list[Path]:
    """Baixa a coleta mais recente de cada tabela para a pasta bruta da fonte."""
    caminhos = []
    with httpx.Client(
        follow_redirects=True, timeout=60, headers={"User-Agent": USER_AGENT}, transport=transport
    ) as http:
        for tabela in tabelas:
            nome = nome_no_armazenamento(fonte, tabela)
            resposta = http.get(
                f"https://github.com/{REPOSITORIO}/releases/download/{RELEASE}/{nome}"
            )
            if resposta.status_code == 404:
                raise ArmazenamentoError(f"Não há coleta guardada de {fonte}/{tabela} na release.")
            resposta.raise_for_status()
            destino = dir_bruto / fonte / f"{tabela}.parquet"
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(resposta.content)
            caminhos.append(destino)
    return caminhos
