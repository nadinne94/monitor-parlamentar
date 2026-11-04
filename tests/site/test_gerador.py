from datetime import date, datetime

import duckdb
import pytest

from monitor.site.gerador import (
    DadosSite,
    Parlamentar,
    carregar_dados,
    chave_ordenacao,
    formatar_data_hora,
    formatar_mes,
    renderizar,
)


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


def test_chave_ordenacao_ignora_acentos_e_caixa():
    nomes = ["Zé Vitor", "Álvaro", "ana", "Aécio Neves", "Éder"]

    ordenados = sorted(nomes, key=chave_ordenacao)

    assert ordenados == ["Aécio Neves", "Álvaro", "ana", "Éder", "Zé Vitor"]


def parlamentar(id_fonte, nome, partido="PT", url_foto=None):
    return Parlamentar(id_fonte=id_fonte, nome=nome, partido=partido, uf="MG", url_foto=url_foto)


@pytest.fixture
def dados():
    return DadosSite(
        parlamentares=[
            parlamentar("74646", "Aécio Neves", "PSDB", "https://exemplo/74646.jpg"),
            parlamentar("107970", "Ana Paula Leão", "PP"),
        ],
        gerado_em=datetime(2027, 3, 5, 9, 30),
        versao="9.9.9",
    )


def test_index_lista_a_bancada_com_links(tmp_path, dados):
    renderizar(dados, tmp_path)

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "2 deputados em exercício" in html
    assert 'href="deputados/74646.html"' in html
    assert html.index("Aécio Neves") < html.index("Ana Paula Leão")
    assert "05/03/2027 às 09:30" in html
    assert "9.9.9" in html


def test_index_sem_deputados_mostra_estado_vazio(tmp_path):
    renderizar(DadosSite(parlamentares=[]), tmp_path)

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "Nenhum deputado carregado" in html


def test_gera_uma_pagina_por_deputado(tmp_path, dados):
    paginas = renderizar(dados, tmp_path)

    pagina = tmp_path / "deputados" / "74646.html"
    html = pagina.read_text(encoding="utf-8")
    assert len(paginas) == 3
    assert "<h1>Aécio Neves</h1>" in html
    assert "PSDB-MG" in html
    assert 'href="../static/estilo.css"' in html
    assert 'alt="Foto de Aécio Neves"' in html
    assert "https://www.camara.leg.br/deputados/74646" in html


def test_deputado_sem_foto_nao_gera_imagem(tmp_path, dados):
    renderizar(dados, tmp_path)

    html = (tmp_path / "deputados" / "107970.html").read_text(encoding="utf-8")
    assert "<img" not in html


def test_copia_estaticos_e_desativa_jekyll(tmp_path, dados):
    renderizar(dados, tmp_path)

    assert (tmp_path / "static" / "estilo.css").is_file()
    assert (tmp_path / ".nojekyll").is_file()


def test_apaga_build_anterior(tmp_path, dados):
    (tmp_path / "antigo.html").write_text("velho", encoding="utf-8")

    renderizar(dados, tmp_path)

    assert not (tmp_path / "antigo.html").exists()


def criar_dim_parlamentar(caminho, linhas):
    with duckdb.connect(str(caminho)) as conexao:
        conexao.execute(
            "create table dim_parlamentar (id_fonte varchar, nome_parlamentar varchar,"
            " partido_atual varchar, uf varchar, url_foto varchar, em_exercicio boolean)"
        )
        conexao.executemany("insert into dim_parlamentar values (?, ?, ?, ?, ?, ?)", linhas)


def test_carregar_dados_le_quem_esta_em_exercicio_em_ordem(tmp_path):
    caminho = tmp_path / "teste.duckdb"
    criar_dim_parlamentar(
        caminho,
        [
            ("3", "Zé Vitor", "PL", "MG", None, True),
            ("2", "Álvaro", "PT", "MG", None, True),
            ("1", "Ana", "PP", "MG", None, False),
        ],
    )

    dados = carregar_dados(caminho)

    assert [p.nome for p in dados.parlamentares] == ["Álvaro", "Zé Vitor"]
    assert dados.parlamentares[0] == Parlamentar("2", "Álvaro", "PT", "MG", None)


def test_textos_da_api_sao_escapados(tmp_path):
    malicioso = parlamentar("1", "<script>alert(1)</script>")

    renderizar(DadosSite(parlamentares=[malicioso]), tmp_path)

    html = (tmp_path / "deputados" / "1.html").read_text(encoding="utf-8")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
