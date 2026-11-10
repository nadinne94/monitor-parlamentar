from datetime import UTC, date, datetime

import duckdb
import pytest

from monitor.site.gerador import (
    DadosSite,
    Parlamentar,
    Proposicao,
    Votacao,
    Voto,
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
        coletado_em=datetime(2027, 3, 4, 22, 15),
    )


def test_index_lista_a_bancada_com_links(tmp_path, dados):
    renderizar(dados, tmp_path)

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "2 deputados em exercício" in html
    assert 'href="deputados/74646.html"' in html
    assert html.index("Aécio Neves") < html.index("Ana Paula Leão")
    assert "coletados em 04/03/2027 às 22:15" in html
    assert "Site gerado em 05/03/2027 às 09:30" in html
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


COLETA = datetime(2026, 11, 6, 13, 30, tzinfo=UTC)


def criar_banco(caminho, parlamentares, proposicoes=()):
    """Um banco mínimo, só com as colunas que o site lê da dim_parlamentar e do fato."""
    with duckdb.connect(str(caminho)) as conexao:
        conexao.execute(
            "create table dim_parlamentar (parlamentar_sk varchar, id_fonte varchar,"
            " nome_parlamentar varchar, partido_atual varchar, uf varchar, url_foto varchar,"
            " em_exercicio boolean, _carregado_em timestamptz)"
        )
        conexao.execute(
            "create table fato_proposicao (parlamentar_sk varchar, mes_ref date,"
            " tipo_sigla varchar, numero integer, ano integer, ementa varchar,"
            " tipo_categoria varchar, papel_autoria varchar, data_apresentacao date)"
        )
        conexao.executemany(
            "insert into dim_parlamentar values (?, ?, ?, ?, ?, ?, ?, ?)", parlamentares
        )
        if proposicoes:
            conexao.executemany(
                "insert into fato_proposicao values (?, ?, ?, ?, ?, ?, ?, ?, ?)", proposicoes
            )


def test_carregar_dados_le_quem_esta_em_exercicio_em_ordem(tmp_path):
    caminho = tmp_path / "teste.duckdb"
    criar_banco(
        caminho,
        [
            ("sk3", "3", "Zé Vitor", "PL", "MG", None, True, COLETA),
            ("sk2", "2", "Álvaro", "PT", "MG", None, True, COLETA),
            ("sk1", "1", "Ana", "PP", "MG", None, False, COLETA),
        ],
    )

    dados = carregar_dados(caminho)

    assert [p.nome for p in dados.parlamentares] == ["Álvaro", "Zé Vitor"]
    assert dados.parlamentares[0] == Parlamentar("2", "Álvaro", "PT", "MG", None)
    assert formatar_data_hora(dados.coletado_em) == "06/11/2026 às 10:30"


def test_carregar_dados_le_as_proposicoes_e_os_meses(tmp_path):
    caminho = tmp_path / "teste.duckdb"
    outubro, setembro = date(2026, 10, 1), date(2026, 9, 1)
    criar_banco(
        caminho,
        [("sk1", "1", "Ana", "PT", "MG", None, True, COLETA)],
        [
            ("sk1", setembro, "PL", 10, 2026, "Antigo", "legislativa", "autor", date(2026, 9, 3)),
            ("sk1", outubro, "PL", 20, 2026, "Novo", "legislativa", "autor", date(2026, 10, 9)),
            ("sk1", outubro, "PRL", 1, 0, "Parecer", "relatoria", "autor", date(2026, 10, 9)),
        ],
    )

    dados = carregar_dados(caminho)

    assert dados.meses == [outubro, setembro]
    assert [p.identificacao for p in dados.parlamentares[0].proposicoes] == [
        "PL 20/2026",
        "PL 10/2026",
    ]


def test_textos_da_api_sao_escapados(tmp_path):
    malicioso = parlamentar("1", "<script>alert(1)</script>")

    renderizar(DadosSite(parlamentares=[malicioso]), tmp_path)

    html = (tmp_path / "deputados" / "1.html").read_text(encoding="utf-8")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


OUTUBRO = date(2026, 10, 1)
SETEMBRO = date(2026, 9, 1)


def proposicao(numero, categoria="legislativa", papel="autor", mes=OUTUBRO, sigla="PL"):
    return Proposicao(mes, sigla, numero, 2026, f"Ementa {numero}", categoria, papel)


def test_do_mes_filtra_por_mes_categoria_e_papel():
    p = Parlamentar(
        "1",
        "Ana",
        "PT",
        "MG",
        None,
        proposicoes=(
            proposicao(1),
            proposicao(2, papel="coautor"),
            proposicao(3, categoria="requerimento", sigla="REQ"),
            proposicao(4, mes=SETEMBRO),
        ),
    )

    assert [x.numero for x in p.do_mes(OUTUBRO, "legislativa", "autor")] == [1]
    assert [x.numero for x in p.do_mes(OUTUBRO, "legislativa", "coautor")] == [2]
    assert [x.numero for x in p.do_mes(SETEMBRO, "legislativa", "autor")] == [4]


@pytest.fixture
def dados_com_proposicoes():
    ana = Parlamentar(
        "1",
        "Ana",
        "PT",
        "MG",
        None,
        proposicoes=(
            proposicao(10),
            proposicao(11, papel="coautor"),
            proposicao(12, categoria="requerimento", sigla="REQ"),
        ),
    )
    return DadosSite(parlamentares=[ana], meses=[OUTUBRO, SETEMBRO])


def test_pagina_mostra_as_proposicoes_do_mes_separadas(tmp_path, dados_com_proposicoes):
    renderizar(dados_com_proposicoes, tmp_path)

    html = (tmp_path / "deputados" / "1.html").read_text(encoding="utf-8")
    assert "Projetos apresentados (1)" in html
    assert "<strong>PL 10/2026</strong> Ementa 10" in html
    assert "assinou como coautor (1)" in html
    assert "<strong>REQ 12/2026</strong>" in html


def test_pagina_tem_navegacao_por_mes(tmp_path, dados_com_proposicoes):
    renderizar(dados_com_proposicoes, tmp_path)

    html = (tmp_path / "deputados" / "1.html").read_text(encoding="utf-8")
    assert 'href="#mes-2026-10"' in html
    assert 'id="mes-2026-09"' in html
    assert html.index("outubro de 2026</h3>") < html.index("setembro de 2026</h3>")


def test_mes_sem_proposicoes_diz_que_nao_houve(tmp_path, dados_com_proposicoes):
    renderizar(dados_com_proposicoes, tmp_path)

    html = (tmp_path / "deputados" / "1.html").read_text(encoding="utf-8")
    setembro = html[html.index('id="mes-2026-09"') :]
    assert "Nenhum projeto apresentado neste mês." in setembro


def votacao_exemplo(aprovacao=True):
    return Votacao("1-1", date(2026, 10, 14), "Aprovada a subemenda.", aprovacao)


@pytest.mark.parametrize(
    ("aprovacao", "esperado"), [(True, "Aprovada"), (False, "Rejeitada"), (None, None)]
)
def test_resultado_da_votacao(aprovacao, esperado):
    assert votacao_exemplo(aprovacao).resultado == esperado


@pytest.mark.parametrize(
    ("voto", "esperado"),
    [("sim", "Sim"), ("sem_registro", "Sem voto registrado"), ("artigo_17", "Presidiu a sessão")],
)
def test_rotulo_do_voto(voto, esperado):
    assert Voto(OUTUBRO, votacao_exemplo(), voto).rotulo.startswith(esperado)
