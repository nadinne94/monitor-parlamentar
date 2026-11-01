"""CLI do projeto. O GitHub Actions chama exatamente estes comandos."""

import subprocess
from datetime import datetime
from typing import Annotated

import typer

from monitor.config import DIR_TRANSFORM, fontes_ativas

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


@app.command()
def ingest(
    fonte: Annotated[
        str | None, typer.Option(help="Nome da fonte. Padrão: todas as ativas.")
    ] = None,
    mes: Annotated[
        str | None, typer.Option(help="Mês de referência (AAAA-MM).", callback=validar_mes)
    ] = None,
) -> None:
    """Coleta os dados brutos das fontes ativas."""
    alvo = [f for f in fontes_ativas() if fonte is None or f.nome == fonte]
    for f in alvo:
        typer.echo(f"[ingest] fonte={f.nome} mes={mes or 'atual'}: ainda não implementado.")

    if not alvo:
        typer.echo(f"Nenhuma fonte ativa com o nome '{fonte}'.", err=True)
        raise typer.Exit(code=1)


@app.command()
def transform() -> None:
    """Executa os modelos e testes do dbt."""
    comando = ["dbt", "build", "--project-dir", ".", "--profiles-dir", "."]
    try:
        subprocess.run(comando, cwd=DIR_TRANSFORM, check=True)
    except subprocess.CalledProcessError as erro:
        typer.echo("O dbt build falhou. Veja o log acima.", err=True)
        raise typer.Exit(code=erro.returncode) from None
