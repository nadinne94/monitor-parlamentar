# ADR-003: Contrato canônico de dados

- **Status:** Aceito
- **Data:** 2026-10-30
- **Decisora:** Nadinne
- **Relacionado:** [ADR-001](0001-escopo-do-mvp.md), [ADR-002](0002-stack-tecnologica.md)

## Contexto

O projeto deve crescer por módulos: hoje a Câmara dos Deputados; depois o Senado, câmaras municipais e outras fontes. Cada fonte tem identificadores, nomes de campos, vocabulários e granularidades próprios. Exemplos:

- O voto pode vir como "Sim", "SIM" ou "S"; a obstrução pode nem existir em uma câmara municipal.
- O identificador do parlamentar é um número na API da Câmara, outro no Senado e outro no SAPL.
- Uma câmara municipal não tem cota parlamentar (CEAP).

Se o site e as métricas dependerem diretamente das estruturas de cada fonte, cada fonte nova exige alterar o site, e remover uma fonte quebra consultas. O requisito de "excluir ou acrescentar partes sem atrapalhar o projeto todo" exige uma fronteira estável entre **fontes** e **consumidores**.

## Decisão

### 1. Uma camada de marts é o contrato

Os modelos da camada `marts` do dbt formam o **contrato canônico**. Regras:

- O site (e qualquer consumidor futuro) **só lê tabelas do contrato**. Nunca lê `staging` ou `intermediate`.
- Cada fonte só tem uma obrigação: produzir linhas que obedeçam ao contrato.
- O contrato é imposto tecnicamente com **model contracts do dbt** (`contract: enforced: true`): nomes e tipos de colunas são verificados no build, e o build falha se uma fonte entregar algo fora do esquema.

### 2. Estrutura: dimensões conformadas + um fato por métrica + um resumo

Optou-se por tabelas fato tipadas por métrica, e não por uma única tabela genérica de atividades, porque as quatro métricas têm formatos diferentes (voto tem valor categórico, despesa tem valor monetário e categoria, proposição tem tipo e ementa). Uma tabela genérica perderia tipagem e tornaria os testes de dados fracos.

**Dimensões**

`dim_parlamentar`: uma linha por parlamentar por fonte.

| Coluna | Tipo | Observação |
|---|---|---|
| `parlamentar_sk` | varchar | chave substituta: hash de `fonte` + `id_fonte` |
| `fonte` | varchar | ex.: `camara_api` |
| `id_fonte` | varchar | identificador original na fonte |
| `nome_parlamentar` | varchar | nome de urna / nome parlamentar |
| `nome_civil` | varchar | |
| `casa` | varchar | vocabulário controlado (ver seção 3) |
| `esfera` | varchar | vocabulário controlado |
| `uf` | varchar | |
| `municipio` | varchar | nulo fora da esfera municipal |
| `partido_atual` | varchar | |
| `url_foto` | varchar | |
| `em_exercicio` | boolean | |

`dim_mes`: uma linha por mês de referência (`mes_ref` = primeiro dia do mês), com `ano`, `mes` e `legislatura`.

**Fatos** (grão = um evento atômico)

`fato_proposicao`: uma linha por proposição × parlamentar autor.
Colunas: `proposicao_sk`, `parlamentar_sk`, `mes_ref`, `data_apresentacao`, `tipo_sigla`, `tipo_categoria`, `numero`, `ano`, `ementa`, `papel_autoria`, `url_inteiro_teor`.

`fato_presenca`: uma linha por sessão × parlamentar.
Colunas: `sessao_sk`, `parlamentar_sk`, `mes_ref`, `data_sessao`, `tipo_sessao`, `status_presenca`, `justificativa`.

`fato_voto`: uma linha por votação nominal × parlamentar.
Colunas: `votacao_sk`, `parlamentar_sk`, `mes_ref`, `data_votacao`, `descricao_votacao`, `proposicao_sk` (anulável), `voto`.

`fato_despesa`: uma linha por documento de despesa.
Colunas: `despesa_sk`, `parlamentar_sk`, `mes_ref`, `data_documento`, `categoria`, `categoria_original`, `fornecedor_nome`, `fornecedor_documento`, `valor_documento`, `valor_glosa`, `valor_liquido`, `url_documento`.

**Resumo para o site**

`resumo_mensal_parlamentar`: uma linha por parlamentar × mês. É a tabela que alimenta o topo de cada página.
Colunas: `parlamentar_sk`, `mes_ref`, `qtd_proposicoes`, `qtd_proposicoes_legislativas`, `sessoes_total`, `sessoes_presente`, `ausencias_justificadas`, `taxa_presenca`, `votos_registrados`, `despesa_total`, `mes_fechado`, `atualizado_em`.

**Colunas técnicas em todas as tabelas:** `fonte`, `_carregado_em`, `_versao_contrato`.

### 3. Vocabulários controlados

Campos categóricos aceitam apenas valores fechados, verificados com o teste `accepted_values` do dbt. Cada fonte é responsável por mapear seus valores originais para estes:

| Campo | Valores aceitos |
|---|---|
| `casa` | `camara_deputados`, `senado`, `camara_municipal` |
| `esfera` | `federal`, `municipal` |
| `voto` | `sim`, `nao`, `abstencao`, `obstrucao`, `art17`, `outro` |
| `status_presenca` | `presente`, `ausente`, `ausencia_justificada` |
| `tipo_categoria` | `legislativa`, `requerimento`, `outra` |
| `papel_autoria` | `autor`, `coautor` |

O valor original é sempre preservado nas camadas `staging`, para auditoria. Ampliar um vocabulário é mudança compatível (seção 5).

### 4. Como uma fonte se conecta

Cada fonte é um módulo com três partes:

1. **Ingestão** (`ingestion/<fonte>/`): coleta e valida com Pydantic, grava Parquet bruto.
2. **Staging** (`transform/models/staging/<fonte>/`): limpeza e tipagem, mantendo os nomes originais.
3. **Adaptador** (`transform/models/intermediate/<fonte>/`): um modelo por fato que a fonte fornece, já no formato do contrato (ex.: `int_camara__fato_voto`).

Os marts unem os adaptadores de todas as fontes **ativas**, listadas em `sources.yaml` e repassadas ao dbt como variável. Adicionar uma fonte = criar o módulo e incluí-la na lista. Remover = tirá-la da lista. Nenhum mart, teste ou página do site precisa mudar.

Uma fonte **não precisa fornecer todos os fatos**. Cada fonte declara em `sources.yaml` quais fatos fornece (ex.: uma câmara municipal sem dados de despesa fornece só proposições, presença e votos).

### 5. Ausência de dado não é zero

Regra central para não distorcer leituras: quando uma fonte não fornece uma métrica, o valor no resumo é **nulo**, não zero. O site exibe "dado não disponível para esta casa", nunca "0". Zero só aparece quando a fonte fornece a métrica e de fato não houve ocorrência no mês.

### 6. Versionamento do contrato

O contrato segue versionamento semântico, registrado em `_versao_contrato`:

- **Mudança compatível** (minor): nova coluna anulável, novo valor em vocabulário, nova tabela. Não exige ADR.
- **Mudança incompatível** (major): remover ou renomear coluna, mudar tipo ou grão. Exige novo ADR e uso de versões de modelo do dbt para conviver com a versão anterior durante a transição.

Versão inicial: **1.0.0**.

## Alternativas consideradas

**Tabela única genérica (`atividade_mensal` com `tipo` e `quantidade`).** Rejeitada. Simples de unir, mas perde tipagem, impede testes específicos (ex.: `valor_liquido >= 0` só faz sentido para despesa) e empurra a complexidade para o site.

**Site lendo direto das camadas de staging de cada fonte.** Rejeitada. Acopla o site às fontes, que é exatamente o problema a evitar.

**Star schema completo como no projeto anterior** (dimensões de partido, órgão, proposição etc.). Adiado. Para o MVP, as dimensões de parlamentar e mês bastam. Novas dimensões entram como mudança compatível quando um incremento precisar.

**Identidade única de pessoa entre fontes** (reconhecer que o deputado que virou senador é a mesma pessoa). Adiada. Exige uma chave comum (como CPF), que nem todas as fontes publicam. O MVP tem uma só fonte; resolver em ADR próprio quando o Senado entrar.

## Consequências

**Positivas**

- Fontes entram e saem sem alterar o site.
- Erros de mapeamento de uma fonte são barrados no build, antes de chegar ao público.
- O contrato documenta, em um só lugar, o que o projeto mede e como.
- A regra "nulo não é zero" protege a credibilidade do site.

**Negativas / riscos**

- Mais modelos para escrever por fonte (staging + adaptadores) do que uma integração direta.
- Vocabulários fechados exigem decisões de mapeamento que nem sempre são óbvias (ex.: como uma câmara municipal registra obstrução). Essas decisões devem ser documentadas no adaptador de cada fonte.
- **LGPD:** `fornecedor_documento` pode conter CPF de pessoa física. Embora a Câmara publique esse dado, o site deve exibi-lo mascarado (ex.: `***.456.789-**`). CNPJ pode ser exibido integralmente.
- Confirmar no incremento 1 que model contracts do dbt funcionam como esperado com o adaptador dbt-duckdb.
