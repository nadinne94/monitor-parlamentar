from pathlib import Path

import pytest

from monitor.ingestion.core.erros import ConfiguracaoError
from monitor.ingestion.fontes import (
    INGESTORES,
    TABELAS_FIXAS,
    ingerir_camara_api,
    tabelas_da_fonte,
)


def test_camara_api_esta_registrada():
    assert INGESTORES["camara_api"] is ingerir_camara_api


def test_camara_api_ingere_deputados_e_os_meses_pedidos(tmp_path, monkeypatch):
    chamadas = []

    def deputados_falso(uf: str, destino: Path) -> Path:
        chamadas.append(("deputados", uf))
        return destino

    def proposicoes_falso(cliente, uf: str, mes: str, pasta: Path) -> list[Path]:
        chamadas.append(("proposicoes", uf, mes))
        return [pasta / f"proposicoes_{mes}.parquet", pasta / f"autores_{mes}.parquet"]

    def votacoes_falso(cliente, mes: str, pasta: Path) -> list[Path]:
        chamadas.append(("votacoes", mes))
        return [pasta / f"{tabela}_{mes}.parquet" for tabela in ("votacoes", "votos", "afetadas")]

    monkeypatch.setattr("monitor.ingestion.fontes.ingerir_deputados", deputados_falso)
    monkeypatch.setattr("monitor.ingestion.fontes.ingerir_proposicoes", proposicoes_falso)
    monkeypatch.setattr("monitor.ingestion.fontes.ingerir_votacoes", votacoes_falso)
    meses = ["2026-09", "2026-10"]

    arquivos = ingerir_camara_api({"uf": "MG"}, tmp_path, meses)

    assert chamadas == [
        ("deputados", "MG"),
        ("proposicoes", "MG", "2026-09"),
        ("votacoes", "2026-09"),
        ("proposicoes", "MG", "2026-10"),
        ("votacoes", "2026-10"),
    ]
    assert all(arquivo.parent == tmp_path / "camara_api" for arquivo in arquivos)
    assert [arquivo.stem for arquivo in arquivos] == tabelas_da_fonte("camara_api", meses)


def test_camara_api_sem_uf_e_erro_de_configuracao(tmp_path):
    with pytest.raises(ConfiguracaoError, match="uf"):
        ingerir_camara_api({}, tmp_path, [])


def test_toda_fonte_registrada_declara_suas_tabelas():
    assert set(TABELAS_FIXAS) == set(INGESTORES)


def test_tabelas_da_fonte_inclui_as_mensais_de_cada_mes():
    assert tabelas_da_fonte("camara_api", ["2026-09", "2026-10"]) == [
        "deputados",
        "proposicoes_2026-09",
        "autores_2026-09",
        "votacoes_2026-09",
        "votos_2026-09",
        "afetadas_2026-09",
        "proposicoes_2026-10",
        "autores_2026-10",
        "votacoes_2026-10",
        "votos_2026-10",
        "afetadas_2026-10",
    ]
