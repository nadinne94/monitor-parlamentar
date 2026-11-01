"""CLI do projeto. O GitHub Actions chama exatamente estes comandos."""

import subprocess
from datetime import datetime
from typing import Annotated

import typer

from monitor.config import CAMINHO_DUCKDB, DIR_SAIDA_SITE, DIR_TRANSFORM, fontes_ativas
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


@app.command()
def ingest(
    fonte: Annotated[
        str | None, typer.Option(help="Nome da fonte. Padrão: todas as ativas.")
    ] = None,
    # mes: Annotated[
    #     str | None, typer.Option(help="Mês de referência (AAAA-MM).", callback=validar_mes)
    # ] = None,
    mes: OpcaoMes = None,
) -> None:
    """Coleta os dados brutos das fontes ativas."""
    alvo = [f for f in fontes_ativas() if fonte is None or f.nome == fonte]
    if not alvo:
        typer.echo(f"Nenhuma fonte ativa com o nome '{fonte}'.", err=True)
        raise typer.Exit(code=1)
    for f in alvo:
        typer.echo(f"[ingest] fonte={f.nome} mes={mes or 'atual'}: ainda não implementado.")


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
