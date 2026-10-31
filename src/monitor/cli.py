"""CLI do projeto. O GitHub Actions chama exatamente estes comandos."""

import typer

app = typer.Typer(no_args_is_help=True)


@app.callback()
def principal() -> None:
    """Monitor Parlamentar: pipeline de dados abertos."""


@app.command()
def ingest() -> None:
    """Coleta os dados brutos das fontes ativas."""
