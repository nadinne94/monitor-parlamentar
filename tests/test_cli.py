from typer.testing import CliRunner

from monitor.cli import app

runner = CliRunner()


def test_ajuda_lista_o_comando_ingest():
    resultado = runner.invoke(app, ["--help"])

    assert resultado.exit_code == 0
    assert "ingest" in resultado.output
