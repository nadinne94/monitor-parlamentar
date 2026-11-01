"""Gerador do site estático (ADR-004).

Lê apenas tabelas do contrato canônico no DuckDB e renderiza HTML com Jinja2.
"""

import shutil
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from monitor import __version__

DIR_STATIC = Path(__file__).parent / "static"
FUSO = ZoneInfo("America/Sao_Paulo")

MESES = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def formatar_mes(valor: date) -> str:
    """date(2027, 2, 1) -> 'fevereiro de 2027'."""
    return f"{MESES[valor.month - 1]} de {valor.year}"


def formatar_data_hora(valor: datetime) -> str:
    """datetime(2027, 3, 5, 9, 30) -> '05/03/2027 às 09:30'."""
    return f"{valor:%d/%m/%Y} às {valor:%H:%M}"


@dataclass
class DadosSite:
    """Tudo o que os templates recebem."""

    meses: list[date] = field(default_factory=list)
    gerado_em: datetime = field(default_factory=lambda: datetime.now(FUSO))
    versao: str = __version__


def criar_ambiente() -> Environment:
    ambiente = Environment(
        loader=PackageLoader("monitor.site", "templates"),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    ambiente.filters["mes"] = formatar_mes
    ambiente.filters["data_hora"] = formatar_data_hora
    return ambiente


def renderizar(dados: DadosSite, destino: Path) -> list[Path]:
    """Gera o site em `destino`, apagando o conteúdo anterior. Devolve as páginas geradas."""
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)
    shutil.copytree(DIR_STATIC, destino / "static")

    ambiente = criar_ambiente()
    html = ambiente.get_template("index.html").render(dados=dados)
    pagina = destino / "index.html"
    pagina.write_text(html, encoding="utf-8")

    # Impede o GitHub Pages de processar o site com Jekyll.
    (destino / ".nojekyll").touch()
    return [pagina]
