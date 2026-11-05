# Monitor Parlamentar

Acompanhe, mês a mês, o que os deputados federais de Minas Gerais fizeram:
proposições apresentadas, presença em plenário, votos nominais e gastos da cota parlamentar.

**Site:** https://nadinne94.github.io/monitor-parlamentar/

> **Status:** Incremento 1 concluído. O site mostra a bancada de MG com dados reais da API
> da Câmara, atualizados a cada publicação. Os relatórios mensais começam em fevereiro de 2027.
> Veja o [roadmap](docs/roadmap.md).

## Como funciona

    API da Câmara → ingestão (Python + Pydantic) → Parquet → dbt (staging → intermediate → marts) → site → GitHub Pages

As decisões de arquitetura estão registradas em [`docs/adr/`](docs/adr/), e as investigações que as embasaram, em [`docs/spikes/`](docs/spikes/).

## Como executar

Pré-requisitos: [uv](https://docs.astral.sh/uv/) e Git. O uv instala o Python 3.12 sozinho.

    git clone https://github.com/nadinne94/monitor-parlamentar.git
    cd monitor-parlamentar
    uv sync
    uv run pre-commit install
    uv run pytest
    uv run monitor pipeline

O site é gerado em `build/site/index.html`.

| Comando | O que faz |
|---|---|
| `uv run monitor ingest --mes 2026-09` | Coleta os dados brutos das fontes ativas |
| `uv run monitor transform` | Executa os modelos e testes do dbt |
| `uv run monitor site` | Gera o site estático a partir do banco |
| `uv run monitor pipeline` | Executa as três etapas em sequência |

## Como contribuir

Todo trabalho entra por pull request. Cada PR precisa passar por três verificações
automáticas: qualidade (pre-commit), testes (pytest) e transformação (dbt).
Cada merge na `main` publica o site automaticamente.

## Fonte dos dados

[API de Dados Abertos da Câmara dos Deputados](https://dadosabertos.camara.leg.br/swagger/api.html)

## Licença

MIT
