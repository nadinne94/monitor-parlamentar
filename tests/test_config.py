from pathlib import Path

from monitor.config import carregar_fontes, fontes_ativas


def _escrever(tmp_path: Path, conteudo: str) -> Path:
    caminho = tmp_path / "sources.yaml"
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def test_carrega_fontes_declaradas(tmp_path):
    caminho = _escrever(
        tmp_path,
        """
fontes:
  camara_api:
    ativa: true
    fatos: [fato_voto]
  senado_api:
    ativa: false
""",
    )

    fontes = carregar_fontes(caminho)

    assert [f.nome for f in fontes] == ["camara_api", "senado_api"]
    assert fontes[0].ativa is True
    assert fontes[0].fatos == ("fato_voto",)
    assert fontes[1].fatos == ()


def test_fontes_ativas_ignora_desativadas(tmp_path):
    caminho = _escrever(
        tmp_path,
        """
fontes:
  camara_api: {ativa: true}
  senado_api: {ativa: false}
""",
    )

    ativas = fontes_ativas(caminho)

    assert [f.nome for f in ativas] == ["camara_api"]


def test_arquivo_sem_fontes_devolve_lista_vazia(tmp_path):
    caminho = _escrever(tmp_path, "")

    assert carregar_fontes(caminho) == []


def test_sources_yaml_do_repositorio_e_valido():
    """Garante que o arquivo versionado continua legível."""
    nomes = [f.nome for f in carregar_fontes()]

    assert "camara_api" in nomes
