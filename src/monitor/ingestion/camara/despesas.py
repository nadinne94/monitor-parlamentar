"""Ingestão das despesas da cota parlamentar (ver ADR-009 e docs/spikes/s6-api-despesas.md)."""

from monitor.ingestion.camara.modelos import DespesaApi
from monitor.ingestion.core.cliente import ClienteApi
from monitor.ingestion.core.erros import IngestaoError


def buscar_despesas(cliente: ClienteApi, id_deputado: int, mes: str) -> list[DespesaApi]:
    """Despesas do deputado na competência (AAAA-MM).

    Sempre com ano e mês: sem eles, a API aplica um recorte padrão de cerca de seis meses
    (ADR-009, seção 2).
    """
    ano, numero = (int(parte) for parte in mes.split("-"))
    params = {
        "ano": ano,
        "mes": numero,
        "ordem": "ASC",
        "ordenarPor": "dataDocumento",
        "itens": 100,
    }
    caminho = f"/deputados/{id_deputado}/despesas"
    despesas = [DespesaApi.model_validate(item) for item in cliente.paginar(caminho, params)]
    outras = sorted({f"{d.ano}-{d.mes:02d}" for d in despesas} - {mes})
    if outras:
        raise IngestaoError(
            f"Pedido para {mes}, mas vieram despesas das competências: {', '.join(outras)}."
        )
    return despesas
