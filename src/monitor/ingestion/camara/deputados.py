"""Ingestão da lista de deputados da API da Câmara (ver docs/spikes/s0-api-deputados.md)."""

from monitor.ingestion.camara.modelos import DeputadoApi
from monitor.ingestion.core.cliente import ClienteApi

URL_API_CAMARA = "https://dadosabertos.camara.leg.br/api/v2"


class IngestaoError(Exception):
    """A API respondeu, mas o conteúdo não faz sentido para o projeto."""


def buscar_deputados(cliente: ClienteApi, uf: str) -> list[DeputadoApi]:
    """Deputados em exercício da UF, validados. Falha se a lista vier vazia ou com outra UF."""
    params = {"siglaUf": uf, "ordem": "ASC", "ordenarPor": "nome", "itens": 100}
    deputados = [DeputadoApi.model_validate(item) for item in cliente.paginar("/deputados", params)]

    if not deputados:
        raise IngestaoError(f"A API não devolveu nenhum deputado para a UF {uf}.")
    outras_ufs = sorted({d.sigla_uf for d in deputados if d.sigla_uf != uf})
    if outras_ufs:
        raise IngestaoError(f"Pedido para {uf}, mas vieram deputados de: {', '.join(outras_ufs)}.")
    return deputados
