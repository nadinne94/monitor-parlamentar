"""CLI do projeto. O GitHub Actions chama exatamente estes comandos."""

from typing import Annotated

import typer

from monitor.config import fontes_ativas

app = typer.Typer(no_args_is_help=True)


@app.callback()
def principal() -> None:
    """Monitor Parlamentar: pipeline de dados abertos."""


@app.command()
def ingest(
    fonte: Annotated[
        str | None, typer.Option(help="Nome da fonte. Padrão: todas as ativas.")
    ] = None,
    mes: Annotated[str | None, typer.Option(help="Mês de referência (AAAA-MM).")] = None,
) -> None:
    """Coleta os dados brutos das fontes ativas."""
    alvo = [f for f in fontes_ativas() if fonte is None or f.nome == fonte]
    for f in alvo:
        typer.echo(f"[ingest] fonte={f.nome} mes={mes or 'atual'}: ainda não implementado.")
