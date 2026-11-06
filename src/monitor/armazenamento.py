"""Armazenamento dos dados brutos numa release do GitHub (ADR-006)."""

from datetime import date

REPOSITORIO = "nadinne94/monitor-parlamentar"
RELEASE = "dados-brutos"


def nome_no_armazenamento(fonte: str, tabela: str, dia: date | None = None) -> str:
    """camara_api + deputados -> camara_api__deputados.parquet (com __AAAA-MM-DD se houver dia)."""
    sufixo = f"__{dia.isoformat()}" if dia else ""
    return f"{fonte}__{tabela}{sufixo}.parquet"
