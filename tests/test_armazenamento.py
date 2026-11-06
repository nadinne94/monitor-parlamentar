import subprocess
from datetime import date
from pathlib import Path

import pytest

from monitor.armazenamento import (
    RELEASE,
    REPOSITORIO,
    ArmazenamentoError,
    guardar,
    nome_no_armazenamento,
)


@pytest.mark.parametrize(
    ("dia", "esperado"),
    [
        (None, "camara_api__deputados.parquet"),
        (date(2026, 11, 6), "camara_api__deputados__2026-11-06.parquet"),
    ],
)
def test_nome_no_armazenamento(dia, esperado):
    assert nome_no_armazenamento("camara_api", "deputados", dia) == esperado


@pytest.fixture
def arquivo_bruto(tmp_path):
    arquivo = tmp_path / "bruto" / "camara_api" / "deputados.parquet"
    arquivo.parent.mkdir(parents=True)
    arquivo.write_bytes(b"conteudo do parquet")
    return arquivo


def test_guardar_envia_a_copia_mais_recente_e_a_do_dia(arquivo_bruto):
    chamadas = []

    def executar_falso(comando, **kwargs):
        enviados = [Path(c) for c in comando if c.endswith(".parquet")]
        chamadas.append((comando, kwargs, [p.read_bytes() for p in enviados]))

    nomes = guardar("camara_api", [arquivo_bruto], date(2026, 11, 6), executar=executar_falso)

    comando, kwargs, conteudos = chamadas[0]
    assert comando[:4] == ["gh", "release", "upload", RELEASE]
    assert "--clobber" in comando
    assert comando[-2:] == ["--repo", REPOSITORIO]
    assert kwargs["check"] is True
    assert nomes == ["camara_api__deputados.parquet", "camara_api__deputados__2026-11-06.parquet"]
    assert conteudos == [b"conteudo do parquet", b"conteudo do parquet"]


def test_guardar_falha_vira_erro_de_armazenamento(arquivo_bruto):
    def executar_que_falha(comando, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd=comando)

    with pytest.raises(ArmazenamentoError, match="camara_api"):
        guardar("camara_api", [arquivo_bruto], date(2026, 11, 6), executar=executar_que_falha)
