"""Gera Parquets SINTÉTICOS de votações para o dbt do CI (ver ADR-008).

Os votos são inventados: servem só para exercitar os modelos e os testes de dados.
Os ids dos deputados vêm do Parquet de teste da bancada, mas nenhum voto é real.

Uso: uv run python tests/fixtures/gerar_votacoes_sinteticas.py [pasta]
"""

import sys
from pathlib import Path

import duckdb

from monitor.ingestion.camara.modelos import VotacaoApi, VotoApi
from monitor.ingestion.camara.votacoes import gravar_votacoes, gravar_votos

MES = "2026-10"


def votacao(id_, aprovacao):
    return VotacaoApi.model_validate(
        {
            "id": id_,
            "dataHoraRegistro": "2026-10-14T20:00:00",
            "siglaOrgao": "PLEN",
            "descricao": f"Votação sintética {id_}, só para testes.",
            "aprovacao": aprovacao,
        }
    )


def voto(id_deputado, tipo, uf="MG"):
    return VotoApi.model_validate(
        {
            "tipoVoto": tipo,
            "dataRegistroVoto": "2026-10-14T19:55:00",
            "deputado_": {"id": id_deputado, "nome": "Deputado de teste", "siglaUf": uf},
        }
    )


def main(pasta: Path) -> None:
    ids = [
        linha[0]
        for linha in duckdb.sql(
            f"select id from '{pasta / 'deputados.parquet'}' order by id limit 2"
        ).fetchall()
    ]
    votacoes = [votacao("1-1", 1), votacao("2-1", 0), votacao("3-1", 1)]
    votos = {
        "1-1": [voto(ids[0], "Sim"), voto(ids[1], "Não"), voto(1, "Artigo 17", "PB")],
        "2-1": [voto(ids[0], "Abstenção"), voto(2, "Sim", "SP")],
        "3-1": [],
    }
    gravar_votacoes(votacoes, votos, pasta / f"votacoes_{MES}.parquet")
    gravar_votos(votos, pasta / f"votos_{MES}.parquet")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tests/fixtures/bruto/camara_api"))
