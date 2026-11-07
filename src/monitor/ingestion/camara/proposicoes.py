"""Ingestão das proposições do mês (ver ADR-007 e docs/spikes/s3-api-proposicoes.md)."""

import calendar
from datetime import date

from monitor.ingestion.camara.modelos import ProposicaoApi
from monitor.ingestion.core.cliente import ClienteApi


def limites_do_mes(mes: str) -> tuple[date, date]:
    """'2026-10' -> (date(2026, 10, 1), date(2026, 10, 31))."""
    ano, numero = (int(parte) for parte in mes.split("-"))
    ultimo_dia = calendar.monthrange(ano, numero)[1]
    return date(ano, numero, 1), date(ano, numero, ultimo_dia)


def buscar_proposicoes(cliente: ClienteApi, uf: str, mes: str) -> list[ProposicaoApi]:
    """Proposições apresentadas no mês por deputados da UF."""
    inicio, fim = limites_do_mes(mes)
    params = {
        "siglaUfAutor": uf,
        "dataApresentacaoInicio": inicio.isoformat(),
        "dataApresentacaoFim": fim.isoformat(),
        "ordem": "ASC",
        "ordenarPor": "id",
        "itens": 100,
    }
    return [ProposicaoApi.model_validate(item) for item in cliente.paginar("/proposicoes", params)]
