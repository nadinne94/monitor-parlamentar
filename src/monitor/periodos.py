"""Meses de referência do pipeline (ver ADR-007, seção 4)."""

import calendar
from datetime import date


def meses_a_processar(hoje: date, quantidade: int = 3) -> list[str]:
    """Os últimos `quantidade` meses até o atual (AAAA-MM), do mais antigo ao mais novo."""
    ano, mes = hoje.year, hoje.month
    meses = []
    for _ in range(quantidade):
        meses.append(f"{ano:04d}-{mes:02d}")
        ano, mes = (ano, mes - 1) if mes > 1 else (ano - 1, 12)
    return list(reversed(meses))


def limites_do_mes(mes: str) -> tuple[date, date]:
    """'2026-10' -> (date(2026, 10, 1), date(2026, 10, 31))."""
    ano, numero = (int(parte) for parte in mes.split("-"))
    ultimo_dia = calendar.monthrange(ano, numero)[1]
    return date(ano, numero, 1), date(ano, numero, ultimo_dia)
