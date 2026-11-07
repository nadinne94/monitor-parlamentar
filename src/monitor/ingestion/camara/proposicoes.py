"""Ingestão das proposições do mês (ver ADR-007 e docs/spikes/s3-api-proposicoes.md)."""

import calendar
from datetime import date


def limites_do_mes(mes: str) -> tuple[date, date]:
    """'2026-10' -> (date(2026, 10, 1), date(2026, 10, 31))."""
    ano, numero = (int(parte) for parte in mes.split("-"))
    ultimo_dia = calendar.monthrange(ano, numero)[1]
    return date(ano, numero, 1), date(ano, numero, ultimo_dia)
