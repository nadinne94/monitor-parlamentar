"""Modelos de validação das respostas da API da Câmara dos Deputados.

Descrevem os dados como a API os entrega, com os nomes de campo convertidos para
snake_case. Campos que o projeto não usa são descartados (ver docs/spikes/s0-api-deputados.md).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeputadoApi(BaseModel):
    """Um item da lista `GET /deputados`."""

    model_config = ConfigDict(extra="ignore", frozen=True, str_strip_whitespace=True)

    id: int = Field(gt=0)
    nome: str = Field(min_length=1)
    sigla_uf: str = Field(alias="siglaUf", pattern=r"^[A-Z]{2}$")
    id_legislatura: int = Field(alias="idLegislatura", gt=0)
    sigla_partido: str | None = Field(default=None, alias="siglaPartido")
    url_foto: str | None = Field(default=None, alias="urlFoto")
    email: str | None = None


class ProposicaoApi(BaseModel):
    """Um item da lista `GET /proposicoes` (ver docs/spikes/s3-api-proposicoes.md)."""

    model_config = ConfigDict(extra="ignore", frozen=True, str_strip_whitespace=True)

    id: int = Field(gt=0)
    sigla_tipo: str = Field(alias="siglaTipo", min_length=1)
    cod_tipo: int = Field(alias="codTipo", gt=0)
    numero: int = Field(ge=0)
    ano: int = Field(ge=0)
    ementa: str = ""
    data_apresentacao: datetime = Field(alias="dataApresentacao")


class AutorApi(BaseModel):
    """Um item de `GET /proposicoes/{id}/autores`."""

    model_config = ConfigDict(extra="ignore", frozen=True, str_strip_whitespace=True)

    nome: str = Field(min_length=1)
    tipo: str
    cod_tipo: int = Field(alias="codTipo")
    ordem_assinatura: int = Field(alias="ordemAssinatura", ge=0)
    proponente: bool
    uri: str | None = None

    @property
    def id_deputado(self) -> int | None:
        """O id do deputado, extraído da `uri`. None se o autor não for um deputado."""
        if self.uri is None or "/deputados/" not in self.uri:
            return None
        return int(self.uri.rsplit("/", 1)[-1])
