# ADR-007: Tipos de proposição e autoria

- **Status:** Aceito
- **Data:** 2026-11-07
- **Decisora:** Nadinne
- **Relacionado:** [ADR-001](0001-escopo-do-mvp.md), [ADR-003](0003-contrato-canonico.md), spike S3 (`docs/spikes/s3-api-proposicoes.md`)

## Contexto

O ADR-001 definiu "proposições" como uma das quatro métricas do MVP e deixou em aberto quais tipos contam e como tratar autoria e coautoria. O ADR-003 previu, no `fato_proposicao`, as colunas `tipo_categoria` (`legislativa`, `requerimento`, `outra`) e `papel_autoria` (`autor`, `coautor`).

O spike S3 mostrou que:

- A consulta por UF e por período de apresentação devolve, para a bancada de MG em outubro de 2026, 88 itens de 15 tipos diferentes.
- Só 30 desses itens são projetos (PL, PLP, PDL, PRC). Outros 26 são requerimentos e indicações; 23 são documentos de relatoria (pareceres, substitutivos, redações finais), em que o relator aparece como autor; e 8 são requerimentos de procedimento em plenário.
- A sigla REQ abrange dezenas de finalidades, identificadas pelo `codTipo`, que vem em cada item da lista.
- A autoria vem de um endpoint separado (`/proposicoes/{id}/autores`), com `ordemAssinatura` e `proponente`. Coautores podem ser incluídos depois da apresentação, por requerimento.
- O período de cada consulta não pode passar de 3 meses.

Contar todos os itens juntos misturaria atividades de naturezas diferentes e daria o mesmo peso a um parecer, a um pedido de audiência pública e a um projeto de lei.

## Decisão

### 1. Classificação por categoria

Cada item recebe uma categoria a partir do `siglaTipo`:

| Categoria | Tipos | O que representa |
|---|---|---|
| `legislativa` | PL, PLP, PEC, PDL, PRC | Projetos que propõem mudar a lei, a Constituição ou as regras da Câmara |
| `requerimento` | REQ, RIC, INC | Pedidos, fiscalização e sugestões ao Executivo |
| `relatoria` | PRL, SBT, SBR, RDF, EMP, EMC, EMR | Trabalho do deputado como relator ou na emenda de proposições de outros |
| `procedimental` | RPD, REC | Atos de procedimento em plenário e comissões |
| `outra` | Qualquer outro tipo | Itens que não se encaixam nas categorias acima |

- A tabela de classificação fica num **seed do dbt** (`mapa_tipos_proposicao.csv`): versionada, documentada e fácil de revisar.
- Um tipo que não estiver no seed recebe `outra`, e um teste de dados com severidade de **aviso** sinaliza tipos novos, sem interromper o deploy.
- O vocabulário de `tipo_categoria` do ADR-003 ganha dois valores, `relatoria` e `procedimental`. É uma mudança compatível (seção 5 do ADR-003): o contrato passa à versão 1.1.0.

### 2. O que o site mostra

- **"Proposições apresentadas no mês"** conta só a categoria `legislativa`, com a lista dos projetos e as ementas.
- **"Requerimentos e indicações"** aparecem num bloco separado, com a sua própria contagem.
- `relatoria` e `procedimental` ficam nos dados, mas não são exibidos no MVP. A relatoria é uma atividade relevante e pode virar uma métrica própria no futuro.
- A subdivisão dos requerimentos pelo `codTipo` (audiência pública, homenagem, urgência, informação) fica para depois do MVP.

### 3. Autoria

- O grão do `fato_proposicao` é **proposição × parlamentar** (como no ADR-003): uma proposição com três autores da bancada gera três linhas.
- `papel_autoria` é `autor` para quem tem `ordemAssinatura` 1 e `coautor` para os demais.
- O site exibe separadamente as proposições de **autoria** do deputado e as que ele **assinou como coautor**.
- Só entram no fato os autores que estão na `dim_parlamentar`. Autores de outros estados, comissões e outros órgãos ficam na camada bruta, mas não no fato.

### 4. Coleta

- Uma consulta por mês, para a bancada inteira (`siglaUfAutor=MG`), com as datas de apresentação explícitas.
- Para cada item, uma consulta aos autores. Cerca de 90 requisições por mês, um volume que o cliente HTTP atual suporta.
- Como a autoria pode mudar depois da apresentação, cada execução reprocessa os **últimos 3 meses**.

## Alternativas consideradas

**Contar todos os tipos juntos.** Rejeitada: os documentos de relatoria e os requerimentos superariam os projetos e distorceriam a leitura do mês.

**Descartar na ingestão tudo que não for projeto.** Rejeitada: os dados ficariam incompletos, e a relatoria e os requerimentos não poderiam ser exibidos depois sem uma nova coleta. Classificar e filtrar na exibição mantém as opções abertas.

**Uma consulta por deputado** (`idDeputadoAutor`, 53 por mês). Mantida como alternativa: será adotada se a implementação mostrar que o filtro por UF não traz as coautorias de deputados de MG em proposições de autores de outros estados.

**Somar autoria e coautoria numa única contagem.** Rejeitada: apresentar um projeto e assinar o projeto de outro são contribuições diferentes, e o visitante deve ver a diferença.

## Consequências

**Positivas**
- A métrica de proposições reflete o que o cidadão entende por "o deputado apresentou um projeto".
- Nenhum dado é descartado: outras leituras (relatoria, tipos de requerimento) continuam possíveis.
- A classificação é transparente e revisável, num arquivo versionado.

**Negativas / riscos**
- O significado exato do `proponente` em proposições com vários autores não foi observado no spike. A regra pela `ordemAssinatura` deve ser conferida na implementação, com um caso real de coautoria.
- Não se sabe ainda se o filtro por UF traz coautorias de proposições de autores de outros estados.
- A classificação por sigla pode errar casos de fronteira (um REQ que, na prática, é procedimental). O seed permite corrigir sem mexer no código.
- O reprocessamento de 3 meses multiplica as requisições por três a cada execução.

## Atualização (novembro de 2026)

A primeira coleta de setembro e novembro trouxe cinco tipos sem classificação, todos documentos de relatoria apresentados em Plenário: `PRLP`, `PPP`, `PEP`, `PRLE` e `SSP`. Foram classificados como `relatoria`, como os seus equivalentes de comissão. O teste de aviso funcionou como previsto: sinalizou os tipos novos sem interromper o deploy.
