import subprocess

import duckdb
import httpx
import pytest
from typer.testing import CliRunner

from monitor.armazenamento import ArmazenamentoError
from monitor.cli import app
from monitor.config import DIR_TRANSFORM, Fonte
from monitor.ingestion.core.erros import ConfiguracaoError, IngestaoError

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


"""def test_ingest_sem_filtro_processa_todas_as_ativas(duas_fontes):
    resultado = runner.invoke(app, ["ingest"])

    assert resultado.exit_code == 0
    assert "fonte=camara_api" in resultado.output
    assert "fonte=senado_api" in resultado.output


def test_ingest_com_filtro_processa_so_a_fonte_pedida(duas_fontes):
    resultado = runner.invoke(app, ["ingest", "--fonte", "senado_api", "--mes", "2026-09"])

    assert resultado.exit_code == 0
    assert "fonte=senado_api mes=2026-09" in resultado.output
    assert "camara_api" not in resultado.output
"""


@pytest.fixture
def ingestores_falsos(monkeypatch):
    """Substitui as ingestões reais por funções que só anotam a chamada."""
    chamadas = []

    def falso(nome):
        def ingerir(parametros, dir_bruto):
            chamadas.append(nome)
            return [dir_bruto / nome / "dados.parquet"]

        return ingerir

    ingestores = {"camara_api": falso("camara_api"), "senado_api": falso("senado_api")}
    monkeypatch.setattr("monitor.cli.INGESTORES", ingestores)
    return chamadas


def test_ingest_sem_filtro_processa_todas_as_ativas(duas_fontes, ingestores_falsos):
    resultado = runner.invoke(app, ["ingest"])

    assert resultado.exit_code == 0
    assert ingestores_falsos == ["camara_api", "senado_api"]
    assert "fonte=camara_api: gravado" in resultado.output


def test_ingest_com_filtro_processa_so_a_fonte_pedida(duas_fontes, ingestores_falsos):
    resultado = runner.invoke(app, ["ingest", "--fonte", "senado_api"])

    assert resultado.exit_code == 0
    assert ingestores_falsos == ["senado_api"]


def test_ingest_fonte_sem_ingestao_implementada_falha(duas_fontes, monkeypatch):
    monkeypatch.setattr("monitor.cli.INGESTORES", {})

    resultado = runner.invoke(app, ["ingest"])

    assert resultado.exit_code == 1
    assert "não tem ingestão implementada" in resultado.output


@pytest.mark.parametrize(
    "erro",
    [
        IngestaoError("lista vazia"),
        ConfiguracaoError("falta a uf"),
        httpx.ConnectError("sem rede"),
    ],
)
def test_ingest_falha_da_fonte_vira_falha_da_cli(duas_fontes, monkeypatch, erro):
    def ingerir_que_falha(parametros, dir_bruto):
        raise erro

    monkeypatch.setattr("monitor.cli.INGESTORES", {"camara_api": ingerir_que_falha})

    resultado = runner.invoke(app, ["ingest", "--fonte", "camara_api"])

    assert resultado.exit_code == 1
    assert str(erro) in resultado.output


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


def test_site_sem_banco_falha_com_orientacao(tmp_path, monkeypatch):
    monkeypatch.setattr("monitor.cli.CAMINHO_DUCKDB", tmp_path / "nao_existe.duckdb")

    resultado = runner.invoke(app, ["site"])

    assert resultado.exit_code == 1
    assert "Rode `monitor transform` antes" in resultado.output


def test_site_gera_paginas_a_partir_do_banco(tmp_path, monkeypatch):
    banco = tmp_path / "teste.duckdb"
    with duckdb.connect(str(banco)) as conexao:
        conexao.execute(
            "create table dim_parlamentar as select '74646' as id_fonte,"
            " 'Aécio Neves' as nome_parlamentar, 'PSDB' as partido_atual, 'MG' as uf,"
            " null::varchar as url_foto, true as em_exercicio"
        )
    saida = tmp_path / "site"
    monkeypatch.setattr("monitor.cli.CAMINHO_DUCKDB", banco)
    monkeypatch.setattr("monitor.cli.DIR_SAIDA_SITE", saida)

    resultado = runner.invoke(app, ["site"])

    assert resultado.exit_code == 0
    assert "Aécio Neves" in (saida / "index.html").read_text(encoding="utf-8")


def test_pipeline_executa_as_etapas_em_ordem(monkeypatch):
    etapas = []
    monkeypatch.setattr("monitor.cli.ingest", lambda **kwargs: etapas.append("ingest"))
    monkeypatch.setattr("monitor.cli.transform", lambda: etapas.append("transform"))
    monkeypatch.setattr("monitor.cli.site", lambda: etapas.append("site"))

    resultado = runner.invoke(app, ["pipeline", "--mes", "2026-09"])

    assert resultado.exit_code == 0
    assert etapas == ["ingest", "transform", "site"]


@pytest.fixture
def armazenamento_falso(monkeypatch):
    """Substitui guardar e recuperar por funções que só anotam as chamadas."""
    chamadas = []

    def guardar(fonte, arquivos, dia):
        chamadas.append(("guardar", fonte, [a.name for a in arquivos]))
        return [f"{fonte}__dados.parquet"]

    def recuperar(fonte, tabelas, dir_bruto):
        chamadas.append(("recuperar", fonte, tabelas))
        return [dir_bruto / fonte / f"{tabela}.parquet" for tabela in tabelas]

    monkeypatch.setattr("monitor.cli.guardar", guardar)
    monkeypatch.setattr("monitor.cli.recuperar", recuperar)
    monkeypatch.setattr("monitor.cli.TABELAS", {"camara_api": ["deputados"]})
    return chamadas


def test_ingest_com_armazenamento_guarda_a_coleta(
    duas_fontes, ingestores_falsos, armazenamento_falso
):
    resultado = runner.invoke(app, ["ingest", "--fonte", "camara_api", "--armazenamento"])

    assert resultado.exit_code == 0
    assert armazenamento_falso == [("guardar", "camara_api", ["dados.parquet"])]
    assert "guardado na release" in resultado.output


def test_ingest_sem_armazenamento_nao_guarda(duas_fontes, ingestores_falsos, armazenamento_falso):
    resultado = runner.invoke(app, ["ingest", "--fonte", "camara_api"])

    assert resultado.exit_code == 0
    assert armazenamento_falso == []


def test_ingest_falha_se_nao_consegue_guardar(duas_fontes, ingestores_falsos, monkeypatch):
    def guardar_que_falha(fonte, arquivos, dia):
        raise ArmazenamentoError("Falha ao enviar")

    monkeypatch.setattr("monitor.cli.guardar", guardar_que_falha)

    resultado = runner.invoke(app, ["ingest", "--fonte", "camara_api", "--armazenamento"])

    assert resultado.exit_code == 1
    assert "Falha ao enviar" in resultado.output


@pytest.mark.parametrize("erro", [IngestaoError("lista vazia"), httpx.ConnectError("sem rede")])
def test_ingest_usa_a_ultima_coleta_quando_a_api_falha(
    duas_fontes, monkeypatch, armazenamento_falso, erro
):
    def ingerir_que_falha(parametros, dir_bruto):
        raise erro

    monkeypatch.setattr("monitor.cli.INGESTORES", {"camara_api": ingerir_que_falha})

    resultado = runner.invoke(app, ["ingest", "--fonte", "camara_api", "--armazenamento"])

    assert resultado.exit_code == 0
    assert armazenamento_falso == [("recuperar", "camara_api", ["deputados"])]
    assert "Usando a última coleta guardada" in resultado.output


def test_ingest_erro_de_configuracao_nao_usa_coleta_guardada(
    duas_fontes, monkeypatch, armazenamento_falso
):
    def ingerir_mal_configurado(parametros, dir_bruto):
        raise ConfiguracaoError("falta a uf")

    monkeypatch.setattr("monitor.cli.INGESTORES", {"camara_api": ingerir_mal_configurado})

    resultado = runner.invoke(app, ["ingest", "--fonte", "camara_api", "--armazenamento"])

    assert resultado.exit_code == 1
    assert armazenamento_falso == []


def test_ingest_falha_se_nao_ha_coleta_guardada(duas_fontes, monkeypatch, armazenamento_falso):
    def ingerir_que_falha(parametros, dir_bruto):
        raise IngestaoError("lista vazia")

    def recuperar_sem_coleta(fonte, tabelas, dir_bruto):
        raise ArmazenamentoError("Não há coleta guardada")

    monkeypatch.setattr("monitor.cli.INGESTORES", {"camara_api": ingerir_que_falha})
    monkeypatch.setattr("monitor.cli.recuperar", recuperar_sem_coleta)

    resultado = runner.invoke(app, ["ingest", "--fonte", "camara_api", "--armazenamento"])

    assert resultado.exit_code == 1
    assert "Não há coleta guardada" in resultado.output
