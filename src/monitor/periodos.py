"""Meses de referência do pipeline (ver ADR-007, seção 4)."""

from datetime import date


def meses_a_processar(hoje: date, quantidade: int = 3) -> list[str]:
    """Os últimos `quantidade` meses até o atual (AAAA-MM), do mais antigo ao mais novo."""
    ano, mes = hoje.year, hoje.month
    meses = []
    for _ in range(quantidade):
        meses.append(f"{ano:04d}-{mes:02d}")
        ano, mes = (ano, mes - 1) if mes > 1 else (ano - 1, 12)
    return list(reversed(meses))
