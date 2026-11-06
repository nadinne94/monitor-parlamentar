"""CLI do projeto. O GitHub Actions chama exatamente estes comandos."""

import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import httpx
import typer

from monitor.armazenamento import ArmazenamentoError, guardar, recuperar
from monitor.config import (
    CAMINHO_DUCKDB,
    DIR_BRUTO,
    DIR_SAIDA_SITE,
    DIR_TRANSFORM,
    fontes_ativas,
)
from monitor.ingestion.core.erros import ConfiguracaoError, IngestaoError
from monitor.ingestion.fontes import INGESTORES, TABELAS
from monitor.site.gerador import carregar_dados, renderizar

app = typer.Typer(no_args_is_help=True)


@app.callback()
def principal() -> None:
    """Monitor Parlamentar: pipeline de dados abertos."""


def validar_mes(valor: str | None) -> str | None:
    """Aceita None ou um mês no formato AAAA-MM."""
    if valor is None:
        return None
    try:
        datetime.strptime(valor, "%Y-%m")
    except ValueError:
        raise typer.BadParameter("use o formato AAAA-MM, por exemplo 2026-09.") from None
    return valor


OpcaoMes = Annotated[
    str | None, typer.Option(help="Mês de referência (AAAA-MM).", callback=validar_mes)
]

OpcaoArmazenamento = Annotated[
    bool,
    typer.Option(
        "--armazenamento",
        help="Guarda cada coleta na release e, se a API falhar, usa a última guardada (ADR-006).",
    ),
]


@app.command()
def ingest(
    fonte: Annotated[
        str | None, typer.Option(help="Nome da fonte. Padrão: todas as ativas.")
    ] = None,
    mes: OpcaoMes = None,
    armazenamento: OpcaoArmazenamento = False,
) -> None:
    """Coleta os dados brutos das fontes ativas."""
    alvo = [f for f in fontes_ativas() if fonte is None or f.nome == fonte]
    if not alvo:
        typer.echo(f"Nenhuma fonte ativa com o nome '{fonte}'.", err=True)
        raise typer.Exit(code=1)
    for f in alvo:
        ingestor = INGESTORES.get(f.nome)
        if ingestor is None:
            typer.echo(
                f"A fonte '{f.nome}' está ativa, mas não tem ingestão implementada.", err=True
            )
            raise typer.Exit(code=1)
        try:
            arquivos = ingestor(f.parametros, DIR_BRUTO)
        except (IngestaoError, httpx.HTTPError) as erro:
            if not armazenamento:
                typer.echo(f"[ingest] fonte={f.nome}: falhou. {erro}", err=True)
                raise typer.Exit(code=1) from None
            typer.echo(
                f"[ingest] fonte={f.nome}: falhou. Usando a última coleta guardada.", err=True
            )
            arquivos = _recuperar_ou_falhar(f.nome)
        except ConfiguracaoError as erro:
            typer.echo(f"[ingest] fonte={f.nome}: falhou. {erro}", err=True)
            raise typer.Exit(code=1) from None
        else:
            if armazenamento:
                _guardar_ou_falhar(f.nome, arquivos)
        for arquivo in arquivos:
            typer.echo(f"[ingest] fonte={f.nome}: gravado {arquivo}")


def _guardar_ou_falhar(fonte: str, arquivos: list[Path]) -> None:
    try:
        nomes = guardar(fonte, arquivos, datetime.now(UTC).date())
    except ArmazenamentoError as erro:
        typer.echo(f"[ingest] fonte={fonte}: {erro}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"[ingest] fonte={fonte}: guardado na release ({', '.join(nomes)})")


def _recuperar_ou_falhar(fonte: str) -> list[Path]:
    try:
        return recuperar(fonte, TABELAS[fonte], DIR_BRUTO)
    except (ArmazenamentoError, httpx.HTTPError) as erro:
        typer.echo(f"[ingest] fonte={fonte}: sem coleta para usar no lugar. {erro}", err=True)
        raise typer.Exit(code=1) from None


@app.command()
def transform() -> None:
    """Executa os modelos e testes do dbt."""
    comando = ["dbt", "build", "--project-dir", ".", "--profiles-dir", "."]
    try:
        subprocess.run(comando, cwd=DIR_TRANSFORM, check=True)
    except subprocess.CalledProcessError as erro:
        typer.echo("O dbt build falhou. Veja o log acima.", err=True)
        raise typer.Exit(code=erro.returncode) from None


@app.command()
def site() -> None:
    """Gera o site estático em build/site a partir do banco."""
    if not CAMINHO_DUCKDB.exists():
        typer.echo(
            f"Banco não encontrado em {CAMINHO_DUCKDB}. Rode `monitor transform` antes.",
            err=True,
        )
        raise typer.Exit(code=1)
    paginas = renderizar(carregar_dados(CAMINHO_DUCKDB), DIR_SAIDA_SITE)
    typer.echo(f"Site gerado em {DIR_SAIDA_SITE} ({len(paginas)} página(s)).")


@app.command()
def pipeline(mes: OpcaoMes = None) -> None:
    """Executa ingestão, transformação e geração do site, em sequência."""
    ingest(fonte=None, mes=mes)
    transform()
    site()
