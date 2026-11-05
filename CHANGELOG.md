# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
As versões seguem o [roadmap](docs/roadmap.md).

## [0.1.0] - Incremento 1: deputados de MG

### Adicionado
- Spike da API de deputados da Câmara (`docs/spikes/s0-api-deputados.md`).
- ADR-005: a persistência dos dados brutos foi adiada para antes do Incremento 4.
- Cliente HTTP genérico, com novas tentativas em falhas temporárias e de rede, e paginação pelo link `next`.
- Modelo Pydantic do deputado, com validação dos campos essenciais e descarte de campos desconhecidos.
- Ingestão dos deputados de MG para Parquet, com esquema explícito e proteções contra lista vazia e UF errada.
- Testes contra a API real gravados em cassetes, que não guardam respostas de erro do servidor.
- Registro de ingestões por fonte e parâmetros das fontes no `sources.yaml`.
- `monitor ingest` coleta os dados reais da API da Câmara.
- Camadas do dbt (staging, intermediate e marts) e as primeiras tabelas do contrato canônico, `dim_parlamentar` e `dim_mes`, com contratos e testes de dados.
- Job do dbt no CI com um Parquet de teste, sem acesso à API.
- Site lista a bancada de MG em ordem alfabética e gera uma página por deputado.

### Alterado
- O deploy passa a coletar os dados reais da API a cada publicação.

### Removido
- Modelo de exemplo do dbt (`exemplo_meses`), substituído pela `dim_mes`.

## [0.0.1] - Incremento 0: esqueleto andante

### Adicionado
- ADRs 001 (escopo do MVP), 002 (stack), 003 (contrato canônico) e 004 (gerador de site próprio) e roadmap.
- Projeto Python com uv, pre-commit (Ruff e verificações de arquivos) e normalização de fim de linha.
- CI com três verificações obrigatórias: qualidade, testes e dbt.
- Proteção da `main`: alterações só por pull request, com as verificações aprovadas.
- Configuração de fontes de dados via `sources.yaml`.
- CLI `monitor` com os comandos `ingest`, `transform`, `site` e `pipeline`.
- Projeto dbt com DuckDB e modelo de exemplo com contrato e testes de dados.
- Gerador de site estático em Python e Jinja2, com modo claro e escuro.
- Publicação automática do site no GitHub Pages a cada merge na `main`.
