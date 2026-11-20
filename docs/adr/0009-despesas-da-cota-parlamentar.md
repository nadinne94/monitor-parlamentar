# ADR-009: Despesas da cota parlamentar (CEAP)

- **Status:** Aceito
- **Data:** 2026-11-20
- **Decisora:** Nadinne
- **Relacionado:** [ADR-001](0001-escopo-do-mvp.md), [ADR-003](0003-contrato-canonico.md), [ADR-006](0006-persistencia-em-release-do-github.md), [ADR-007](0007-tipos-de-proposicao-e-autoria.md), spike S6 (`docs/spikes/s6-api-despesas.md`)

## Contexto

O ADR-001 definiu as despesas da cota parlamentar como uma das quatro métricas do MVP e deixou em aberto o mês de cada despesa e quando um mês está "fechado". O ADR-003 registrou o risco do CPF de fornecedor pessoa física. O spike S6 mostrou que:

- A Câmara publica as despesas de duas formas: um endpoint por deputado na API e um arquivo anual com todos os deputados. **Só a API traz as passagens aéreas emitidas pelo SIGEPA**, que somaram R$ 1,39 milhão na bancada de MG em seis meses.
- **A API publica o valor líquido com o sinal invertido** em quase todas as categorias (7.751 de 9.100 despesas), sem documentar isso. O arquivo anual traz o gasto como valor positivo. As exceções são as passagens aéreas, com o sinal esperado nas duas fontes, e a complementação do auxílio-moradia, com o sinal oposto ao das demais categorias nas duas fontes.
- Há negativos legítimos: créditos de passagens SIGEPA, com documento e líquido negativos.
- Um documento pode ser dividido entre categorias, e cada linha repete o valor do documento inteiro.
- O filtro de mês da API usa a competência. Em 94% das despesas, a data do documento é do mesmo mês da competência; a data falta em telefonia e no auxílio-moradia.
- A norma dá 90 dias, depois do fornecimento do produto ou serviço, para apresentar o comprovante (Ato da Mesa 43/2009, art. 4º, § 12).
- 82 despesas (0,9%) têm fornecedor pessoa física, identificado por CPF. O comprovante digitalizado mostra o CPF por inteiro e, no exemplo aberto, dados pessoais da própria deputada. 39 nomes de empresas contêm um CPF.
- O `codDocumento` não identifica uma despesa sozinho: as passagens SIGEPA têm um GUID e repetem códigos, e 71 despesas de telefonia têm o código `0`.

Despesas são o tema mais sujeito a insinuações. Um valor com o sinal errado, um mês incompleto apresentado como completo ou um dado de pessoa física exposto podem ser injustos com pessoas reais.

## Decisão

### 1. Fonte

- **O endpoint por deputado da API** (`/deputados/{id}/despesas`), para todas as categorias.
- O arquivo anual não é usado na ingestão. Continua útil para conferências manuais, como no spike.

### 2. Coleta

- Uma consulta por deputado e mês, **sempre com `ano` e `mes`**: sem eles, a API aplica um recorte padrão de cerca de seis meses.
- Páginas de 100 itens, o máximo que a API aceita.
- Cada execução reprocessa os **últimos 4 meses** (o atual e os 3 anteriores), e não os 3 do ADR-007: um mês só fecha cerca de três meses depois de terminar (seção 4) e precisa ser coletado de novo até lá.

### 3. O mês de referência

`mes_ref` é a **competência** informada pela fonte (`ano` e `mes`), e não a data do documento. É o recorte que a própria API e o arquivo anual usam, e a data do documento falta em algumas categorias.

### 4. Mês fechado

- A **data de fechamento** de um mês é o seu último dia mais **90 dias**, o prazo da norma para apresentar o comprovante. Um mês está **fechado** quando a data da coleta é posterior à data de fechamento. Exemplo: outubro de 2026 tem data de fechamento em 29/01/2027 e aparece como fechado nas coletas a partir de 30/01/2027.
- A conta usa a data da coleta (`_carregado_em`), e não a data de hoje, para que o mesmo dado bruto dê sempre o mesmo resultado, inclusive no CI.
- O critério vem da norma, e não da observação. A segunda coleta do spike (27/11/2026) e o histórico diário da release (ADR-006) vão mostrar a defasagem real; se ela for diferente, este ADR é atualizado.
- Fechado quer dizer que acabou o prazo para novos comprovantes. A norma não fixa prazo para glosas, então um valor de um mês fechado ainda pode mudar.

### 5. O valor

- O valor de cada despesa é o **líquido**, o que de fato saiu da cota. O total do mês soma o líquido, **nunca o valor do documento**, que se repete nos documentos divididos entre categorias.
- O sinal do líquido é corrigido por categoria pelo seed `mapa_categorias_despesa.csv`:

| Coluna | Significado |
|---|---|
| `categoria_original` | o texto da fonte, como `COMBUSTÍVEIS E LUBRIFICANTES.` |
| `categoria` | o nome exibido no site, como `Combustíveis e lubrificantes` |
| `sinal` | `-1` quando a API publica o gasto como negativo; `1` quando já o publica como positivo |
| `permite_negativo` | `true` só nas categorias em que um valor negativo é esperado depois da correção |

- A convenção adotada é a do arquivo anual da Câmara: gasto positivo, crédito negativo. A complementação do auxílio-moradia segue o sinal do arquivo anual (negativo), embora a fonte não explique por quê (seção 10).
- O valor original da API é preservado na camada de staging, para auditoria.

### 6. Dados pessoais (LGPD)

Os dados brutos são publicados na release (ADR-006). Por isso, a proteção acontece **na ingestão, antes de gravar o Parquet**, e não no dbt nem no site:

- **CPF de fornecedor** (documento com 11 dígitos): mascarado no formato `***.456.789-**`, previsto no ADR-003.
- **Nome do fornecedor pessoa física:** não é guardado.
- **Link do comprovante de fornecedor pessoa física:** não é guardado, porque a imagem mostra o CPF por inteiro.
- **CPF dentro do nome de uma empresa** (comum em MEI): mascarado no mesmo formato.
- Cada regra tem teste unitário, e um teste de dados verifica que nenhuma coluna de texto do `fato_despesa` contém um CPF sem máscara.

### 7. O modelo

- **`fato_despesa`**: uma linha por **lançamento** (documento × categoria), com as colunas do ADR-003. O grão do ADR-003 ("uma linha por documento") fica mais preciso: um documento dividido entre categorias gera um lançamento por categoria.
- **`despesa_sk`**: hash da fonte, do deputado, da competência, do `codDocumento`, da categoria original, do número, da data e dos valores do documento, mais a ordem entre lançamentos idênticos. O `codDocumento` sozinho não basta.
- **`resumo_despesas_mes`**: uma linha por parlamentar × mês, com `despesa_total`, `qtd_despesas`, `data_fechamento` e `mes_fechado`. Segue o caminho do `resumo_votacoes_mes` (ADR-008): o `resumo_mensal_parlamentar` previsto no ADR-003 não foi criado, e cada métrica tem o próprio resumo.
- Um mês sem despesas de um deputado tem `despesa_total = 0`, porque a fonte fornece a métrica (ADR-003, seção 5).
- As duas tabelas entram no contrato canônico, uma mudança compatível pela seção 6 do ADR-003. O contrato passa à versão 1.3.0.

### 8. Testes de dados

Cada premissa tirada dos dados reais tem um teste que para o build no dia em que deixar de valer:

- Toda categoria original está no seed.
- O sinal publicado pela API é o previsto no seed: líquido negativo ou zero nas categorias com sinal `-1`; nas categorias com sinal `1`, o mesmo sinal do valor do documento.
- Depois da correção, um valor negativo só aparece em categorias com `permite_negativo`. Este teste substitui o `valor_liquido >= 0` do roadmap.
- A glosa nunca é negativa.
- A `despesa_sk` é única.
- Nenhum CPF sem máscara no `fato_despesa`.

### 9. O que o site mostra

- Um bloco "Gastos da cota" na página do deputado, para cada mês: o total e o valor de cada categoria, com o nome legível do seed e o número de lançamentos.
- Quando o mês está aberto, um aviso: a Câmara ainda pode receber comprovantes até a data de fechamento, e os valores podem mudar.
- Um link para a página do deputado no portal da Câmara, onde estão os comprovantes oficiais.
- **Sem** fornecedores, sem links para comprovantes, sem comparação com o limite da cota, sem comparações entre deputados e sem rankings.

### 10. Pontos em aberto

- O significado do sinal da complementação do auxílio-moradia. Pode ser perguntado à Câmara (Fale Conosco ou Lei de Acesso à Informação); até lá, segue o arquivo anual.
- A defasagem real dos lançamentos, a confirmar com a segunda coleta e com o histórico da release.

## Alternativas consideradas

**Arquivo anual como fonte principal, com a API só para as passagens SIGEPA.** Rejeitada. Como a API não filtra por categoria, as passagens exigiriam as mesmas consultas por deputado da opção escolhida, mais o download e a leitura de um arquivo de 48 MB, uma segunda forma de ingestão e o descarte de mais dados pessoais (o CPF do deputado e o nome de passageiros). A única vantagem, trazer os deputados que saíram da bancada, vem para todas as métricas no Incremento 6.

**Só o arquivo anual.** Rejeitada: deixaria de fora as passagens aéreas SIGEPA, e o total do mês ficaria subestimado sem aviso.

**Corrigir o sinal com uma regra geral, como o sinal do valor do documento.** Rejeitada: o auxílio-moradia não tem valor de documento, e uma regra geral esconderia a premissa num cálculo, em vez de deixá-la num seed testado.

**A data do documento como mês de referência.** Rejeitada: falta em telefonia e no auxílio-moradia, e não é o recorte da fonte.

**Medir a defasagem antes de definir o mês fechado.** Adiada: a medida direta exige coletas em dias diferentes. O critério da norma é conhecido e conservador, e a medição pode, no máximo, antecipar o fechamento.

**Exibir os fornecedores no MVP.** Adiada: aumenta o risco de expor pessoas físicas e de leituras insinuativas, e o roadmap pede só o total e as categorias. O cruzamento com os dados de CNPJ já está no backlog.

**Mascarar o CPF só no site.** Rejeitada: os dados brutos são públicos na release.

## Consequências

**Positivas**
- O valor de cada categoria pode ser conferido no arquivo oficial da Câmara (menos as passagens SIGEPA).
- Se a Câmara corrigir o sinal na API, o build falha, em vez de o site mostrar o sinal errado.
- Nenhum CPF completo, nome ou comprovante de pessoa física sai do pipeline.
- A ingestão segue o padrão das outras fontes: cliente HTTP, Pydantic e cassetes.

**Negativas / riscos**
- As despesas de deputados que saíram da bancada ficam de fora até o Incremento 6, como nas outras métricas.
- O reprocessamento de 4 meses faz cerca de 212 consultas por execução (53 × 4), mais as páginas extras. No spike, 318 consultas levaram 44 segundos.
- Um mês fica aberto por cerca de três meses. O relatório de fevereiro de 2027 vai mostrar as despesas com o aviso de mês aberto até o fim de maio de 2027.
- O seed precisa ser atualizado quando surgir uma categoria nova; o build avisa.
