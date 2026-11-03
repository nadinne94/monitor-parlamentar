"""Modelos de validação das respostas da API da Câmara dos Deputados.

Descrevem os dados como a API os entrega, com os nomes de campo convertidos para
snake_case. Campos que o projeto não usa são descartados (ver docs/spikes/s0-api-deputados.md).
"""

from pydantic import BaseModel, ConfigDict, Field


class DeputadoApi(BaseModel):
    """Um item da lista `GET /deputados`."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: int
    nome: str
    sigla_uf: str = Field(alias="siglaUf")
    id_legislatura: int = Field(alias="idLegislatura")
    sigla_partido: str | None = Field(default=None, alias="siglaPartido")
    url_foto: str | None = Field(default=None, alias="urlFoto")
    email: str | None = None
