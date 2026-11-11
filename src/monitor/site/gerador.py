"""Gerador do site estático (ADR-004).

Lê apenas tabelas do contrato canônico no DuckDB e renderiza HTML com Jinja2.
"""

import shutil
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb
from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from monitor import __version__

DIR_STATIC = Path(__file__).parent / "static"
FUSO = ZoneInfo("America/Sao_Paulo")
PRIMEIRO_MES = date(2027, 2, 1)
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


def chave_ordenacao(texto: str) -> str:
    """Chave para ordenar nomes como uma pessoa ordenaria: sem acento e sem caixa."""
    decomposto = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return sem_acento.casefold()


ROTULOS_VOTO = {
    "sim": "Sim",
    "nao": "Não",
    "abstencao": "Abstenção",
    "obstrucao": "Obstrução",
    "artigo_17": "Presidiu a sessão (art. 17 do Regimento)",
    "sem_registro": "Sem voto registrado",
}


@dataclass(frozen=True)
class Votacao:
    """Uma linha da dim_votacao, com o que o site exibe."""

    id_fonte: str
    data: date
    descricao: str
    aprovacao: bool | None

    @property
    def resultado(self) -> str | None:
        """'Aprovada', 'Rejeitada' ou None, quando a fonte não informa (ADR-008)."""
        if self.aprovacao is None:
            return None
        return "Aprovada" if self.aprovacao else "Rejeitada"


@dataclass(frozen=True)
class Voto:
    """Uma linha do fato_voto, com a votação a que pertence."""

    mes_ref: date
    votacao: Votacao
    voto: str

    @property
    def rotulo(self) -> str:
        return ROTULOS_VOTO[self.voto]


@dataclass(frozen=True)
class ResumoVotacoes:
    """Quantas votações o Plenário fez no mês, e quantas foram nominais."""

    plenario: int
    nominais: int


@dataclass(frozen=True)
class Proposicao:
    """Uma linha do fato_proposicao, com o que o site exibe."""

    mes_ref: date
    sigla: str
    numero: int
    ano: int
    ementa: str
    categoria: str
    papel: str

    @property
    def identificacao(self) -> str:
        """'PL 5620/2026'."""
        return f"{self.sigla} {self.numero}/{self.ano}"


@dataclass(frozen=True)
class Parlamentar:
    """Uma linha da dim_parlamentar, com o que o site exibe."""

    id_fonte: str
    nome: str
    partido: str | None
    uf: str
    url_foto: str | None
    proposicoes: tuple[Proposicao, ...] = ()
    votos: tuple[Voto, ...] = ()

    def do_mes(self, mes: date, categoria: str, papel: str) -> list[Proposicao]:
        """As proposições do mês, de uma categoria e de um papel de autoria."""
        return [
            p
            for p in self.proposicoes
            if p.mes_ref == mes and p.categoria == categoria and p.papel == papel
        ]

    def votos_do_mes(self, mes: date) -> list[Voto]:
        """Os votos do parlamentar nas votações nominais do mês."""
        return [v for v in self.votos if v.mes_ref == mes]


@dataclass
class DadosSite:
    """Tudo o que os templates recebem."""

    parlamentares: list[Parlamentar] = field(default_factory=list)
    gerado_em: datetime = field(default_factory=lambda: datetime.now(FUSO))
    versao: str = __version__
    primeiro_mes: date = PRIMEIRO_MES
    coletado_em: datetime | None = None
    meses: list[date] = field(default_factory=list)
    resumo_votacoes: dict[date, ResumoVotacoes] = field(default_factory=dict)


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
    paginas = [_gravar(ambiente, "index.html", destino / "index.html", dados=dados, raiz="")]

    (destino / "deputados").mkdir()
    for parlamentar in dados.parlamentares:
        pagina = destino / "deputados" / f"{parlamentar.id_fonte}.html"
        paginas.append(
            _gravar(ambiente, "deputado.html", pagina, dados=dados, raiz="../", p=parlamentar)
        )

    # Impede o GitHub Pages de processar o site com Jekyll.
    (destino / ".nojekyll").touch()
    return paginas


def _gravar(ambiente: Environment, template: str, arquivo: Path, **contexto) -> Path:
    arquivo.write_text(ambiente.get_template(template).render(**contexto), encoding="utf-8")
    return arquivo


def carregar_dados(caminho_duckdb: Path) -> DadosSite:
    """Lê os parlamentares em exercício, em ordem alfabética, com proposições e votos."""
    consulta_parlamentares = """
        select parlamentar_sk, id_fonte, nome_parlamentar, partido_atual, uf, url_foto
        from dim_parlamentar
        where em_exercicio
    """
    consulta_proposicoes = """
        select parlamentar_sk, mes_ref, tipo_sigla, numero, ano, ementa,
               tipo_categoria, papel_autoria
        from fato_proposicao
        where tipo_categoria in ('legislativa', 'requerimento')
        order by data_apresentacao desc, numero desc
    """
    consulta_votos = """
        select f.parlamentar_sk, f.mes_ref, d.id_fonte, d.data_votacao, d.descricao,
               d.aprovacao, f.voto
        from fato_voto as f
        inner join dim_votacao as d using (votacao_sk)
        order by d.data_votacao desc, d.id_fonte desc
    """
    consulta_meses = """
        select mes_ref from fato_proposicao
        union
        select mes_ref from resumo_votacoes_mes
        order by mes_ref desc
    """
    with duckdb.connect(str(caminho_duckdb), read_only=True) as conexao:
        linhas = conexao.execute(consulta_parlamentares).fetchall()
        linhas_proposicoes = conexao.execute(consulta_proposicoes).fetchall()
        linhas_votos = conexao.execute(consulta_votos).fetchall()
        meses = [mes for (mes,) in conexao.execute(consulta_meses).fetchall()]
        resumo = {
            mes: ResumoVotacoes(plenario, nominais)
            for mes, plenario, nominais in conexao.execute(
                "select mes_ref, votacoes_plenario, votacoes_nominais from resumo_votacoes_mes"
            ).fetchall()
        }
        (coletado_em,) = conexao.execute(
            "select max(_carregado_em) from dim_parlamentar"
        ).fetchone()

    proposicoes = defaultdict(list)
    for sk, *campos in linhas_proposicoes:
        proposicoes[sk].append(Proposicao(*campos))

    votos = defaultdict(list)
    for sk, mes_ref, *campos_votacao, voto in linhas_votos:
        votos[sk].append(Voto(mes_ref, Votacao(*campos_votacao), voto))

    parlamentares = sorted(
        (
            Parlamentar(*campos, proposicoes=tuple(proposicoes[sk]), votos=tuple(votos[sk]))
            for sk, *campos in linhas
        ),
        key=lambda p: chave_ordenacao(p.nome),
    )
    return DadosSite(
        parlamentares=parlamentares,
        coletado_em=coletado_em.astimezone(FUSO) if coletado_em else None,
        meses=meses,
        resumo_votacoes=resumo,
    )
