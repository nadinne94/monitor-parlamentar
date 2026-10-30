# ADR-002: Stack tecnológica

- **Status:** Aceito. A decisão sobre o site está em revisão no [ADR-004](0004-gerador-de-site-proprio.md)
- **Data:** 2026-10-30
- **Decisora:** Nadinne
- **Relacionado:** [ADR-001](0001-escopo-do-mvp.md)

## Contexto

O projeto anterior (`projeto_api_dados_abertos_camara`) usou Databricks, PySpark, Delta Lake e outras ferramentas em período de teste gratuito. Quando os testes expiraram, o acesso aos recursos foi perdido e o pipeline deixou de ser executável.

Requisitos para este projeto:

- **Custo zero permanente:** nada que dependa de trial ou de cartão de crédito.
- **Executável localmente:** o pipeline inteiro deve rodar na máquina da desenvolvedora com um único comando. A nuvem serve só para agendamento e hospedagem.
- **Testável desde o primeiro commit:** a stack precisa facilitar testes unitários, de integração e de qualidade de dados.
- **Modular:** fontes de dados entram e saem sem afetar o resto (ver contrato canônico, ADR-003).
- **Volume pequeno:** dados legislativos de uma bancada estadual somam MBs; mesmo o Brasil inteiro fica na casa de poucos GBs. Processamento distribuído não é necessário.
- **Operação mensal autônoma:** o pipeline deve rodar e publicar sozinho.

## Decisão

| Função | Escolha |
|---|---|
| Linguagem | Python 3.12 |
| Gerência de dependências e ambiente | uv (com `uv.lock` versionado) |
| Cliente HTTP | httpx, com retry e backoff via tenacity |
| Validação na ingestão | Pydantic (um model por recurso da API) |
| Formato de armazenamento | Parquet, particionado por fonte e mês |
| Motor analítico | DuckDB |
| Transformação e modelagem | dbt-core com adaptador dbt-duckdb |
| Testes de código | pytest, pytest-recording (VCR) para gravar respostas da API, pytest-cov |
| Testes de dados | testes nativos do dbt (`not_null`, `unique`, `relationships`, `accepted_values`) + dbt-expectations quando necessário |
| Qualidade de código | Ruff (lint e format), pre-commit |
| CI/CD e orquestração | GitHub Actions |
| Site | Evidence.dev (site estático gerado a partir de SQL) |
| Hospedagem do site | GitHub Pages |
| Persistência dos dados brutos | Hugging Face Datasets (repositório público) |

### Detalhamento

**DuckDB + Parquet em vez de Spark + Delta Lake.** O volume não justifica processamento distribuído. DuckDB roda embutido no processo Python, sem servidor, lê Parquet diretamente e tem desempenho de sobra para GBs. Parquet é um formato aberto, legível por qualquer ferramenta, o que evita aprisionamento a fornecedor.

**dbt para transformação.** Organiza as transformações em camadas (`staging` → `intermediate` → `marts`), gera documentação e linhagem automaticamente e traz testes de dados declarativos. A camada `staging` tem um subdiretório por fonte, o que materializa a modularidade.

**Pydantic na fronteira da ingestão.** Cada resposta da API é validada contra um model antes de ser gravada. Se a API mudar um campo, o pipeline falha cedo e com mensagem clara, em vez de propagar dados quebrados até o site.

**pytest-recording para testes de ingestão.** As respostas reais da API são gravadas uma vez em "cassetes" versionados no repositório. O CI roda contra as cassetes, sem depender da disponibilidade da API, de forma rápida e determinística.

**Evidence.dev para o site.** Gera um site estático a partir de consultas SQL e Markdown. Suporta páginas parametrizadas (uma página por deputado a partir de um único template), o que atende diretamente o ADR-001. Site estático significa nenhum servidor, banco de dados ou custo de hospedagem.

**GitHub Actions como orquestrador.** Três workflows:

- `ci.yml`: em todo push e pull request, roda Ruff, pytest e `dbt build` contra dados de teste. Bloqueia merge se falhar.
- `pipeline.yml`: agendado (cron), executa ingestão → dbt → build do site.
- `deploy.yml`: publica o site no GitHub Pages após pipeline bem-sucedido na `main`.

**Hugging Face Datasets para dados brutos.** Os dados brutos de cada execução precisam persistir entre execuções do pipeline (para reprocessamento e para preservar o histórico, já que a API pode alterar dados retroativamente). Um repositório público de datasets é gratuito, versionado e serve também como publicação aberta dos dados tratados.

### Princípio de execução local

Todo o pipeline é acessível por uma CLI única:

```
uv run monitor ingest --fonte camara --mes 2026-09
uv run monitor transform
uv run monitor site
uv run monitor pipeline --mes 2026-09   # tudo em sequência
```

O GitHub Actions apenas chama esses mesmos comandos. Não existe lógica que só rode na nuvem.

## Alternativas consideradas

**Databricks Community / Free Edition.** Rejeitada. Repete a dependência de plataforma que causou a perda do projeto anterior, e o pipeline não roda fora dela.

**Pandas puro sem dbt.** Rejeitada. Funciona, mas exige construir à mão testes de dados, documentação e linhagem que o dbt já oferece. Polars pode ser usado pontualmente dentro da ingestão, se necessário.

**Airflow, Dagster ou Prefect.** Adiadas. Trazem infraestrutura (servidor, banco de metadados) desproporcional para um pipeline mensal com poucas etapas. Reavaliar se o número de fontes e dependências crescer a ponto de o GitHub Actions ficar difícil de manter.

**Streamlit (Community Cloud).** Rejeitada para o site. Exige servidor em execução, hiberna sem uso e é pensado para exploração interna, não para páginas públicas indexáveis por buscadores.

**Observable Framework.** Alternativa viável ao Evidence, com mais liberdade visual e mais JavaScript. Evidence foi preferido por ser centrado em SQL, mais próximo da experiência da desenvolvedora com BI.

**Commitar os dados no próprio repositório do código.** Rejeitada. Infla o histórico do Git a cada execução e mistura código com dados.

**Cloudflare R2 ou outro object storage.** Alternativa de reserva para os dados brutos caso o Hugging Face não atenda. Exige cadastro de cartão em alguns provedores, o que contraria o requisito de custo zero sem risco.

## Consequências

**Positivas**

- Custo zero sem prazo de expiração.
- Pipeline reproduzível em qualquer máquina com `uv sync`.
- Testes rodam em segundos, sem rede.
- Stack enxuta e moderna, bem alinhada ao mercado (dbt e DuckDB são muito procurados).
- Dados publicados abertamente, coerente com o propósito de transparência do projeto.

**Negativas / riscos**

- **Cron do GitHub Actions desativado por inatividade:** em repositórios públicos, workflows agendados são desativados após 60 dias sem atividade no repositório. Mitigação: monitorar e manter commits regulares; avaliar um workflow de keepalive se necessário.
- **Atraso nos lançamentos da CEAP:** despesas são lançadas com defasagem. Mitigação: rodar o pipeline semanalmente reprocessando os últimos 3 meses, em vez de uma única execução mensal.
- **Evidence.dev é uma ferramenta mais jovem** que soluções tradicionais de BI. Mitigação: o site só lê os marts do dbt; trocar de ferramenta de site não afeta o pipeline.
- **Limites do Hugging Face para datasets** precisam ser confirmados no incremento 1. Se houver impedimento, usar GitHub Releases como armazenamento dos snapshots brutos.
- **Sem Spark no currículo deste projeto.** Aceitável: o projeto anterior já demonstra Spark, e escolher a ferramenta adequada ao volume também é uma competência a demonstrar.

**Validações a fazer no incremento 1**

- Confirmar que a geração de páginas parametrizadas do Evidence funciona com o volume da bancada de MG.
- Confirmar o fluxo de leitura e escrita no Hugging Face Datasets a partir do GitHub Actions (token em GitHub Secrets).
- Medir o tempo total do pipeline no Actions.
