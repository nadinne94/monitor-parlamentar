from datetime import date, datetime

import pytest

from monitor.site.gerador import DadosSite, formatar_data_hora, formatar_mes, renderizar


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (date(2027, 2, 1), "fevereiro de 2027"),
        (date(2027, 3, 1), "março de 2027"),
        (date(2026, 12, 1), "dezembro de 2026"),
    ],
)
def test_formatar_mes(valor, esperado):
    assert formatar_mes(valor) == esperado


def test_formatar_data_hora():
    assert formatar_data_hora(datetime(2027, 3, 5, 9, 30)) == "05/03/2027 às 09:30"


@pytest.fixture
def dados():
    return DadosSite(
        meses=[date(2027, 2, 1), date(2027, 3, 1)],
        gerado_em=datetime(2027, 3, 5, 9, 30),
        versao="9.9.9",
    )


def test_index_mostra_meses_data_e_versao(tmp_path, dados):
    renderizar(dados, tmp_path)

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "fevereiro de 2027" in html
    assert "março de 2027" in html
    assert "05/03/2027 às 09:30" in html
    assert "9.9.9" in html


def test_index_sem_meses_mostra_estado_vazio(tmp_path):
    renderizar(DadosSite(meses=[]), tmp_path)

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "Nenhum mês disponível" in html


def test_copia_estaticos_e_desativa_jekyll(tmp_path, dados):
    renderizar(dados, tmp_path)

    assert (tmp_path / "static" / "estilo.css").is_file()
    assert (tmp_path / ".nojekyll").is_file()


def test_apaga_build_anterior(tmp_path, dados):
    (tmp_path / "antigo.html").write_text("velho", encoding="utf-8")

    renderizar(dados, tmp_path)

    assert not (tmp_path / "antigo.html").exists()
