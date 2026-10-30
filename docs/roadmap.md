# Roadmap do MVP

Referências: [ADR-001 Escopo](adr/0001-escopo-do-mvp.md) · [ADR-002 Stack](adr/0002-stack-tecnologica.md) · [ADR-003 Contrato](adr/0003-contrato-canonico.md) · [ADR-004 Site](adr/0004-gerador-de-site-proprio.md)

## Meta

Ter o site no ar, atualizando sozinho, a tempo da nova legislatura: **pipeline operando em fevereiro de 2027** e **primeiro relatório oficial (fevereiro/2027) publicado no início de março de 2027**.

Estimativas em semanas consideram dedicação parcial (cerca de 8 a 10 horas por semana). Ajustar conforme o ritmo real; as datas são referência, não compromisso.

## Princípios

- **Fatia vertical:** cada incremento vai da API até o site publicado. Ao fim de cada um, existe algo funcionando no ar.
- **Risco primeiro:** dúvidas técnicas são resolvidas em spikes curtos *antes* do incremento que depende delas.
- **Cada incremento é uma versão:** tag `v0.N.0` no Git ao concluir.
- **Nenhum incremento começa com o anterior pela metade.**

## Definição de pronto (vale para todos os incrementos)

Um incremento só está pronto quando:

- [ ] Todo o código entrou na `main` via pull request, com CI verde.
- [ ] Ruff sem erros; pre-commit ativo.
- [ ] Testes unitários para a lógica nova (ingestão, validação, mapeamentos).
- [ ] Testes de ingestão rodam contra cassetes gravadas, sem acesso à rede.
- [ ] Modelos dbt novos têm contrato aplicado (quando forem marts) e testes de dados.
- [ ] `uv run monitor pipeline` funciona localmente do zero.
- [ ] Templates novos do site cobertos por testes.
- [ ] Site publicado no GitHub Pages refletindo a entrega.
- [ ] Documentação atualizada (README, metodologia ou ADR, conforme o caso).
- [ ] Tag de versão criada e entrada no `CHANGELOG.md`.

## Spikes (investigação, sem código de produção)

Cada spike tem duração máxima de 1 dia e termina com uma nota em `docs/spikes/` registrando o que foi descoberto.

| Spike | Pergunta a responder | Antes de |
|---|---|---|
| **S1: Presença na API** | Qual endpoint da API da Câmara representa melhor a presença em sessões deliberativas do plenário? Como aparecem ausências justificadas? | Incremento 5 (mas fazer cedo, durante o Incremento 1) |
| **S2: Persistência no Hugging Face** | É possível ler e gravar Parquet num dataset do Hugging Face a partir do GitHub Actions, com token em Secrets? Há limites que afetem o projeto? | Incremento 1 |
| **S3: Câmara municipal** | A câmara da cidade usa SAPL? Há API ou exportação em formato aberto? O que a prefeitura oferece? | Pós-MVP (pode ser feito a qualquer momento, como pausa) |

## Incrementos

### Incremento 0: Esqueleto andante · `v0.0.1`
**Estimativa:** 1 a 2 semanas · **Alvo:** meados de novembro/2026

**Objetivo:** provar que o caminho completo funciona, ainda sem dados reais.

**Escopo**
- Repositório com estrutura de pastas, `pyproject.toml`, `uv.lock`, `.gitignore`, `.env.example`.
- Ruff + pre-commit configurados.
- pytest com um teste trivial.
- Projeto dbt vazio conectado ao DuckDB, com um modelo de exemplo.
- Gerador de site em Python + Jinja2 (ADR-004) com uma página "em construção".
- CLI `monitor` com comandos vazios (`ingest`, `transform`, `site`, `pipeline`).
- `ci.yml`: lint + testes + `dbt build` em todo PR.
- `deploy.yml`: publica o site no GitHub Pages.
- Pasta `docs/adr/` com os três ADRs aceitos.

**Pronto quando:** um push na `main` deixa o CI verde e a página "em construção" aparece no endereço público.

---

### Incremento 1: Deputados de MG · `v0.1.0`
**Estimativa:** 2 semanas · **Alvo:** fim de novembro/2026
**Depende de:** S2

**Objetivo:** primeira fatia real, que valida a arquitetura inteira.

**Escopo**
- `ingestion/core/`: cliente HTTP genérico com retry, backoff, paginação e log estruturado. **É a parte mais testada do projeto.**
- Ingestão da lista de deputados de MG, validada com Pydantic, gravada em Parquet.
- Persistência dos dados brutos no Hugging Face.
- Modelos dbt: staging da Câmara → adaptador → `dim_parlamentar` e `dim_mes` com contrato aplicado.
- `sources.yaml` com a fonte `camara_api` ativa.
- Site: página inicial com a lista da bancada e uma página por deputado (nome, foto, partido), gerada por template.
- `pipeline.yml` com disparo manual (`workflow_dispatch`).

**Pronto quando:** o pipeline disparado no Actions coleta, transforma e publica as páginas de todos os deputados de MG.

---

### Incremento 2: Proposições · `v0.2.0`
**Estimativa:** 2 semanas · **Alvo:** meados de dezembro/2026

**Antes de começar:** ADR-005 definindo quais tipos de proposição contam (`tipo_categoria`) e como tratar autoria x coautoria.

**Escopo**
- Ingestão das proposições de autoria dos deputados de MG.
- `fato_proposicao` com contrato e testes (`accepted_values` em `tipo_categoria` e `papel_autoria`).
- Primeira versão do `resumo_mensal_parlamentar` (colunas de proposição; demais nulas).
- Site: bloco "Proposições do mês" na página do deputado, com navegação entre meses.

**Pronto quando:** é possível abrir a página de um deputado, escolher um mês de 2026 e ver as proposições apresentadas.

---

### Incremento 3: Votos nominais · `v0.3.0`
**Estimativa:** 2 semanas · **Alvo:** fim de dezembro/2026

**Escopo**
- Ingestão das votações nominais do plenário e dos votos individuais.
- Mapeamento dos valores da API para o vocabulário de `voto`, com teste unitário para cada valor.
- `fato_voto` com contrato e testes.
- Resumo: coluna `votos_registrados`.
- Site: bloco "Como votou", listando cada votação do mês e o voto do deputado.

**Pronto quando:** a página mostra os votos do mês com descrição legível de cada votação.

---

### Incremento 4: Despesas da cota parlamentar · `v0.4.0`
**Estimativa:** 2 semanas · **Alvo:** meados de janeiro/2027

**Escopo**
- Ingestão das despesas da CEAP.
- `fato_despesa` com contrato e testes (ex.: `valor_liquido >= 0`).
- Mascaramento de CPF de fornecedor pessoa física (teste unitário obrigatório).
- Regra de `mes_fechado`: um mês só é marcado como fechado após o período de defasagem definido (documentar o critério).
- Resumo: coluna `despesa_total`.
- Site: bloco "Gastos da cota", total do mês e detalhamento por categoria, com aviso quando o mês ainda não está fechado.

**Pronto quando:** a página mostra os gastos por categoria, sem CPF exposto, e sinaliza meses em aberto.

---

### Incremento 5: Presença · `v0.5.0`
**Estimativa:** 2 semanas · **Alvo:** fim de janeiro/2027
**Depende de:** S1

**Por que por último:** é a métrica com maior risco de interpretação (ausências justificadas, tipos de sessão). O spike S1 resolve a dúvida técnica cedo; a implementação vem quando o restante já está estável.

**Antes de começar:** ADR-006 definindo o que conta como sessão, como presença e como ausência justificada.

**Escopo**
- Ingestão de presença conforme definido no ADR-006.
- `fato_presenca` com contrato e testes.
- Resumo: colunas de sessões, presença e ausências justificadas.
- Site: bloco "Presença", sempre separando ausência justificada de ausência.

**Pronto quando:** as quatro métricas do ADR-001 aparecem na página de cada deputado.

---

### Incremento 6: Operação autônoma · `v1.0.0`
**Estimativa:** 1 a 2 semanas · **Alvo:** início de fevereiro/2027

**Objetivo:** transformar o sistema em produto que roda sozinho.

**Escopo**
- `pipeline.yml` agendado semanalmente, reprocessando os últimos 3 meses.
- Falha no pipeline abre automaticamente uma issue no GitHub.
- Página de metodologia no site: o que cada métrica mede, de onde vem, limitações conhecidas e data da última atualização.
- Tratamento da virada de legislatura: testes para deputados que saem, que entram, suplentes e mudança de partido.
- README final do projeto, como no projeto anterior.

**Pronto quando:** o pipeline roda por duas semanas seguidas sem intervenção, e a nova bancada de MG empossada em 1º de fevereiro aparece corretamente no site.

---

### Marco: primeiro relatório oficial
**Início de março/2027:** relatório de fevereiro/2027 publicado. A partir daqui, o projeto entra em operação contínua.

## Depois do MVP (backlog, sem ordem definida)

Cada item vira um novo incremento, com spike e ADR quando necessário:

- Senado Federal (exige ADR sobre identidade de pessoa entre fontes).
- Câmara municipal e prefeitura (depende do spike S3).
- Emendas parlamentares via Portal da Transparência.
- Ampliação para todos os estados.
- Votações em comissões.
- Busca por nome de parlamentar no site.
- Publicação dos marts como dataset aberto documentado.

## Revisão do roadmap

Revisar este documento ao fim de cada incremento: atualizar estimativas com o tempo real gasto e reordenar o backlog se necessário. Mudanças de escopo do MVP exigem atualização do ADR-001.
