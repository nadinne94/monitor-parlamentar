"""Ingestão das votações do Plenário no mês (ver ADR-008 e docs/spikes/s5-api-votacoes.md)."""

from monitor.ingestion.camara.modelos import VotacaoApi, VotoApi
from monitor.ingestion.core.cliente import ClienteApi
from monitor.ingestion.core.erros import IngestaoError
from monitor.periodos import limites_do_mes

ID_PLENARIO = 180


def buscar_votacoes(cliente: ClienteApi, mes: str) -> list[VotacaoApi]:
    """Votações do Plenário no mês. Falha se vierem votações de outras datas."""
    inicio, fim = limites_do_mes(mes)
    params = {
        "idOrgao": ID_PLENARIO,
        "dataInicio": inicio.isoformat(),
        "dataFim": fim.isoformat(),
        "ordem": "ASC",
        "ordenarPor": "dataHoraRegistro",
        "itens": 100,
    }
    votacoes = [VotacaoApi.model_validate(item) for item in cliente.paginar("/votacoes", params)]
    fora_do_mes = [v.id for v in votacoes if not inicio <= v.data_hora_registro.date() <= fim]
    if fora_do_mes:
        raise IngestaoError(
            f"Pedido para {mes}, mas vieram votações de outras datas: {fora_do_mes}."
        )
    return votacoes


def buscar_votos(cliente: ClienteApi, votacoes: list[VotacaoApi]) -> dict[str, list[VotoApi]]:
    """Os votos de cada votação. Uma lista vazia indica uma votação simbólica."""
    return {
        votacao.id: [
            VotoApi.model_validate(item)
            for item in cliente.get_json(f"/votacoes/{votacao.id}/votos")["dados"]
        ]
        for votacao in votacoes
    }
