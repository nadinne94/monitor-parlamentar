from pathlib import Path

import pytest

from monitor.ingestion.core.erros import ConfiguracaoError
from monitor.ingestion.fontes import INGESTORES, TABELAS, ingerir_camara_api


def test_camara_api_esta_registrada():
    assert INGESTORES["camara_api"] is ingerir_camara_api


def test_camara_api_grava_na_pasta_da_fonte(tmp_path, monkeypatch):
    chamadas = []

    def ingerir_falso(uf: str, destino: Path) -> Path:
        chamadas.append((uf, destino))
        return destino

    monkeypatch.setattr("monitor.ingestion.fontes.ingerir_deputados", ingerir_falso)

    arquivos = ingerir_camara_api({"uf": "MG"}, tmp_path)

    destino_esperado = tmp_path / "camara_api" / "deputados.parquet"
    assert chamadas == [("MG", destino_esperado)]
    assert arquivos == [destino_esperado]
    assert [arquivo.stem for arquivo in arquivos] == TABELAS["camara_api"]


def test_camara_api_sem_uf_e_erro_de_configuracao(tmp_path):
    with pytest.raises(ConfiguracaoError, match="uf"):
        ingerir_camara_api({}, tmp_path)


def test_toda_fonte_registrada_declara_suas_tabelas():
    assert set(TABELAS) == set(INGESTORES)
