"""Proteção de dados pessoais antes da gravação dos dados brutos (ver ADR-009, seção 6).

Os dados brutos são publicados numa release do GitHub (ADR-006). Por isso, nenhum CPF
pode chegar ao Parquet sem máscara: a proteção acontece já na ingestão.
"""

import re


def _digitos(texto: str | None) -> str:
    return re.sub(r"\D", "", texto or "")


def mascarar_cpf(cpf: str) -> str:
    """'12345678901' -> '***.456.789-**': só os seis dígitos do meio ficam visíveis (ADR-003)."""
    digitos = _digitos(cpf)
    if len(digitos) != 11:
        raise ValueError(f"Um CPF tem 11 dígitos; o documento recebido tem {len(digitos)}.")
    return f"***.{digitos[3:6]}.{digitos[6:9]}-**"
