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
    sigla_tipo: str = Field(alias="siglaTipo")
    cod_tipo: int = Field(alias="codTipo", gt=0)
    numero: int = Field(ge=0)
    ano: int = Field(ge=0)
    ementa: str = ""
    data_apresentacao: datetime = Field(alias="dataApresentacao")
