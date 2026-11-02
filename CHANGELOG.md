# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
As versões seguem o [roadmap](docs/roadmap.md).

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
