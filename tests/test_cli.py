import subprocess

import pytest
from typer.testing import CliRunner

from monitor.cli import app
from monitor.config import DIR_TRANSFORM, Fonte

runner = CliRunner()


def test_ajuda_lista_o_comando_ingest():
    resultado = runner.invoke(app, ["--help"])

    assert resultado.exit_code == 0
    assert "ingest" in resultado.output


@pytest.fixture
def duas_fontes(monkeypatch):
    fontes = [
        Fonte(nome="camara_api", ativa=True, fatos=()),
        Fonte(nome="senado_api", ativa=True, fatos=()),
    ]
    monkeypatch.setattr("monitor.cli.fontes_ativas", lambda: fontes)


def test_ingest_sem_filtro_processa_todas_as_ativas(duas_fontes):
    resultado = runner.invoke(app, ["ingest"])

    assert resultado.exit_code == 0
    assert "fonte=camara_api" in resultado.output
    assert "fonte=senado_api" in resultado.output


def test_ingest_com_filtro_processa_so_a_fonte_pedida(duas_fontes):
    resultado = runner.invoke(app, ["ingest", "--fonte", "senado_api", "--mes", "2026-09"])

    assert resultado.exit_code == 0
    assert "fonte=senado_api mes=2026-09" in resultado.output
    assert "camara_api" not in resultado.output


def test_ingest_fonte_inexistente_falha(duas_fontes):
    resultado = runner.invoke(app, ["ingest", "--fonte", "nao_existe"])

    assert resultado.exit_code == 1
    assert "Nenhuma fonte ativa" in resultado.output


@pytest.mark.parametrize("mes", ["2026-13", "09-2026", "setembro"])
def test_ingest_rejeita_mes_invalido(duas_fontes, mes):
    resultado = runner.invoke(app, ["ingest", "--mes", mes])

    assert resultado.exit_code == 2


def test_transform_executa_dbt_build_na_pasta_transform(monkeypatch):
    chamadas = []

    def run_falso(comando, **kwargs):
        chamadas.append((comando, kwargs))

    monkeypatch.setattr("monitor.cli.subprocess.run", run_falso)

    resultado = runner.invoke(app, ["transform"])

    assert resultado.exit_code == 0
    comando, kwargs = chamadas[0]
    assert comando[:2] == ["dbt", "build"]
    assert kwargs["cwd"] == DIR_TRANSFORM
    assert kwargs["check"] is True


def test_transform_propaga_falha_do_dbt(monkeypatch):
    def run_que_falha(comando, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd=comando)

    monkeypatch.setattr("monitor.cli.subprocess.run", run_que_falha)

    resultado = runner.invoke(app, ["transform"])

    assert resultado.exit_code == 1
    assert "dbt build falhou" in resultado.output
