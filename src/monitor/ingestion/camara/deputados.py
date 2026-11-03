"""Ingestão da lista de deputados da API da Câmara (ver docs/spikes/s0-api-deputados.md)."""

from monitor.ingestion.camara.modelos import DeputadoApi
from monitor.ingestion.core.cliente import ClienteApi

URL_API_CAMARA = "https://dadosabertos.camara.leg.br/api/v2"


def buscar_deputados(cliente: ClienteApi, uf: str) -> list[DeputadoApi]:
    """Deputados em exercício da UF, validados."""
    return [DeputadoApi.model_validate(item) for item in cliente.paginar("/deputados")]
