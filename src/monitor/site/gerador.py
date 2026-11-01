"""Gerador do site estático (ADR-004).

Lê apenas tabelas do contrato canônico no DuckDB e renderiza HTML com Jinja2.
"""

from datetime import date, datetime

MESES = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def formatar_mes(valor: date) -> str:
    """date(2027, 2, 1) -> 'fevereiro de 2027'."""
    return f"{MESES[valor.month - 1]} de {valor.year}"


def formatar_data_hora(valor: datetime) -> str:
    """datetime(2027, 3, 5, 9, 30) -> '05/03/2027 às 09:30'."""
    return f"{valor:%d/%m/%Y} às {valor:%H:%M}"
