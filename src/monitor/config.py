"""Configuração central: caminhos do projeto e fontes de dados."""

from dataclasses import dataclass
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO_FONTES = RAIZ / "sources.yaml"


@dataclass(frozen=True)
class Fonte:
    nome: str
    ativa: bool
    fatos: tuple[str, ...]


def carregar_fontes(caminho: Path = ARQUIVO_FONTES) -> list[Fonte]:
    """Lê o sources.yaml e devolve a lista de fontes declaradas."""
    conteudo = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    return [
        Fonte(
            nome=nome,
            ativa=bool(cfg.get("ativa", False)),
            fatos=tuple(cfg.get("fatos", [])),
        )
        for nome, cfg in conteudo["fontes"].items()
    ]
