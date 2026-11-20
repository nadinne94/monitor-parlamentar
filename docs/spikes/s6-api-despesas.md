# Spike S6: API de despesas da Câmara (cota parlamentar)

- **Data:** 2026-11-20
- **Pergunta:** como obter as despesas da cota parlamentar (CEAP) da bancada de MG em cada mês, e o que os dados mostram sobre defasagem, glosas, valores negativos, documentos de fornecedor e categorias?
- **Amostra:** 9.100 despesas dos 53 deputados de MG em exercício, competências de junho a novembro de 2026, coletadas em 20/11/2026.

## Endpoint por deputado

```
GET https://dadosabertos.camara.leg.br/api/v2/deputados/{id}/despesas?ano=2026&mes=10&itens=100
```

- **Campos de cada item:** `ano` e `mes` (números: a competência), `tipoDespesa` (a categoria, em texto), `codDocumento` (texto), `tipoDocumento` e `codTipoDocumento`, `dataDocumento` (texto no formato `2026-10-01T00:00:00`), `numDocumento`, `valorDocumento`, `valorGlosa`, `valorLiquido`, `urlDocumento`, `nomeFornecedor`, `cnpjCpfFornecedor`, `numRessarcimento` (vazio na amostra), `codLote` e `parcela`.
- **Página de no máximo 100 itens:** `itens=500` devolveu 100, com um link `next` que volta a `itens=100`.
- **Sem `ano` nem `mes`, a API aplica um recorte padrão:** para o deputado 74646, vieram de maio (14 das 37 despesas do mês) a novembro, cerca dos últimos seis meses. Só com o `ano`, vem o ano inteiro. Como no S3, a ingestão nunca deve depender do comportamento padrão.
- **O filtro `mes` usa a competência, não a data do documento:** `mes=10` trouxe um documento emitido em novembro.
- **`dataDocumento` falta em 96 despesas:** 71 de telefonia e 25 de complementação do auxílio-moradia.
- **`parcela`** é 0 em 9.075 despesas e nula em 25.
- **Volume:** 53 deputados × 6 meses = 318 consultas, mais as páginas extras, em 44 segundos.

## Arquivo anual em lote

```
https://www.camara.leg.br/cotas/Ano-2026.csv.zip
```

- 4,8 MB compactado e 48,8 MB descompactado; CSV separado por `;`. Download em 1,8 segundo.
- Em 20/11/2026, a última modificação era do mesmo dia (06:38 GMT).
- 128.085 linhas de todos os deputados em 2026; 18.030 da bancada de MG (`sgUF`).
- 32 colunas. O deputado é o `ideCadastro`, o mesmo `id` da API; o `nuDeputadoId` é outro identificador. A despesa é o `ideDocumento`, que é o `codDocumento` da API.
- **Dados pessoais além do fornecedor:** a coluna `cpf` traz o CPF do próprio deputado em todas as linhas; `txtPassageiro` (nome do passageiro) está preenchida em 79 linhas de MG e `txtTrecho` em 73.

## Comparação entre a API e o arquivo (MG, junho a novembro)

| | API | Arquivo |
|---|---|---|
| Linhas | 9.100 | 7.944 |
| Passagens aéreas SIGEPA | 1.292 | nenhuma |
| Líquido negativo | 7.932 | 28 |
| Líquido positivo | 1.168 | 7.916 |
| Linhas sem correspondente no outro | 1.292 (todas SIGEPA) | 136 |

- Sem as passagens SIGEPA, as duas fontes têm a mesma base: 9.100 − 1.292 = 7.808 = 7.944 − 136.
- Deputado 74646, outubro: 17 linhas na API, com soma do líquido de −R$ 4.789,84 (incluindo passagens), e 10 no arquivo, com soma de R$ 15.904,16 (sem passagens).
- **As 136 linhas só do arquivo são de 3 deputados que não estão na lista de deputados em exercício hoje.** A coleta pela API, que parte dessa lista, perde as despesas de quem saiu da bancada; o arquivo traz todos.
- **O arquivo não tem nenhuma passagem SIGEPA**, em nenhuma UF e em nenhum mês de 2026. As passagens que ele traz são reembolso (215 linhas), RPA (192), missão oficial (6) e terrestres, marítimas ou fluviais (579). Na bancada de MG, as passagens SIGEPA somam R$ 1.390.127,32 líquidos em seis meses, a terceira maior categoria em valor.

## Defasagem dos lançamentos

- **Prazo da norma:** 90 dias após o fornecimento do produto ou serviço (Ato da Mesa 43/2009, art. 4º, § 12, sem alteração na versão atualizada).
- **Competência e data do documento:** em 8.458 das 9.004 despesas com data (94%), o documento é do mesmo mês da competência. Em 456, é de um ou dois meses depois; em 90, de um a três meses antes.
- **Volume por competência:**

| Competência | Linhas no arquivo | Despesas na API | Deputados com despesa (API) |
|---|---|---|---|
| 2026-01 | 1.290 | | |
| 2026-02 | 1.762 | | |
| 2026-03 | 2.366 | | |
| 2026-04 | 2.226 | | |
| 2026-05 | 2.442 | | |
| 2026-06 | 2.213 | 2.608 | 50 |
| 2026-07 | 2.142 | 2.559 | 51 |
| 2026-08 | 1.453 | 1.690 | 52 |
| 2026-09 | 894 | 970 | 51 |
| 2026-10 | 1.018 | 1.049 | 50 |
| 2026-11 | 224 | 224 | 34 |

- **A curva não separa a defasagem do calendário:** janeiro é recesso, e agosto e setembro coincidem com a campanha eleitoral. Outubro já tem quase tantos deputados com despesa quanto junho; novembro, ainda em andamento, tem 34 de 53.
- **O `codDocumento` não serve como relógio:** a correlação com a data do documento é de 0,028. A estimativa de defasagem por ele foi descartada.
- **Medida direta (segunda coleta):** a fazer em 27/11/2026, com o mesmo script; o resultado entra como uma atualização desta nota.

## Glosas, valores negativos e restituições

- **Na API, o sinal do líquido está invertido em quase todas as categorias:** em 7.751 despesas, `valorLiquido = −(valorDocumento − valorGlosa)`. As exceções, com o sinal esperado (1.316 despesas), são as passagens aéreas (SIGEPA e RPA) e a complementação do auxílio-moradia.
- **No arquivo, o sinal está correto, exceto no auxílio-moradia:** 7.916 líquidos positivos, 28 negativos e nenhum documento negativo. Na junção pelo identificador, 9.109 linhas têm o mesmo valor com o sinal trocado, e só 24 têm o mesmo valor.
- **Negativos com documento negativo:** 173 passagens SIGEPA na API têm documento e líquido negativos, um crédito e não um gasto.
- **Auxílio-moradia:** os 28 negativos do arquivo são todos de complementação do auxílio-moradia (soma de −R$ 59.232,51). Nessa categoria, o sinal é o oposto do das demais nas duas fontes: negativo no arquivo e positivo na API (25 despesas, R$ 46.791,51). A fonte não documenta o significado desse sinal.
- **Glosa:** nunca negativa. 440 despesas com glosa na API (453 no arquivo). A maior soma é em combustíveis (R$ 20.906,15).
- **Um documento pode ser dividido entre categorias:** um documento de R$ 769,10 aparece em duas linhas, manutenção de escritório (líquido de R$ 345,10) e telefonia (R$ 424,00), cada uma com o valor do documento inteiro. Somar `valorDocumento` contaria o documento duas vezes.
- **Restituições:** nenhuma no arquivo (MG, junho a novembro).

## Documentos de fornecedor

- 9.018 despesas com CNPJ (de 53 deputados) e 82 com CPF (de 18 deputados). O documento vem sempre só com dígitos, com 14 ou 11; nenhum vazio.
- As despesas com CPF são 78 de manutenção de escritório e 4 de táxi, pedágio e estacionamento.
- 39 nomes de fornecedores com CNPJ contêm uma sequência no formato de CPF, comum no nome empresarial de um MEI.
- Todas as 82 despesas com CPF têm link para o comprovante; 1.638 com CNPJ não têm.
- **O comprovante expõe dados pessoais por inteiro.** O comprovante aberto (um recibo de aluguel de escritório, digitalizado) mostra o nome, o CPF completo e a assinatura do locador pessoa física. Mostra também dados pessoais da própria deputada: RG, CPF, estado civil e endereço residencial. É uma amostra de um documento, mas basta para ver que o link do comprovante não é neutro.

## Categorias, tipos de documento e chave

| Categoria (como vem da fonte) | Despesas | Deputados |
|---|---|---|
| COMBUSTÍVEIS E LUBRIFICANTES. | 3.496 | 51 |
| SERVIÇO DE TÁXI, PEDÁGIO E ESTACIONAMENTO | 1.428 | 32 |
| PASSAGEM AÉREA - SIGEPA | 1.292 | 51 |
| MANUTENÇÃO DE ESCRITÓRIO DE APOIO À ATIVIDADE PARLAMENTAR | 1.078 | 48 |
| HOSPEDAGEM ,EXCETO DO PARLAMENTAR NO DISTRITO FEDERAL. | 705 | 38 |
| LOCAÇÃO OU FRETAMENTO DE VEÍCULOS AUTOMOTORES | 343 | 45 |
| TELEFONIA | 294 | 39 |
| FORNECIMENTO DE ALIMENTAÇÃO DO PARLAMENTAR | 173 | 16 |
| DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR. | 125 | 36 |
| PASSAGENS TERRESTRES, MARÍTIMAS OU FLUVIAIS | 68 | 13 |
| COMPLEMENTAÇÃO DO AUXÍLIO-MORADIA | 25 | 5 |
| PASSAGEM AÉREA - RPA | 24 | 3 |
| SERVIÇOS POSTAIS | 22 | 8 |
| SERVIÇO DE SEGURANÇA PRESTADO POR EMPRESA ESPECIALIZADA. | 15 | 6 |
| PASSAGEM AÉREA - REEMBOLSO | 6 | 5 |
| ASSINATURA DE PUBLICAÇÕES | 2 | 2 |
| LOCAÇÃO OU FRETAMENTO DE AERONAVES | 2 | 1 |
| AQUISIÇÃO DE TOKENS E CERTIFICADOS DIGITAIS | 1 | 1 |
| PARTICIPAÇÃO EM CURSO, PALESTRA OU EVENTO SIMILAR | 1 | 1 |

- **19 categorias** em seis meses, escritas de forma irregular na fonte (ponto final em algumas, "HOSPEDAGEM ,EXCETO").
- **Tipos de documento:** 0 Nota Fiscal (6.582), 1 Recibos/Outros (1.946) e 4 DANFE/DACTE (572).
- **O `codDocumento` não identifica uma despesa sozinho:** há 8.873 códigos distintos para 9.100 despesas. As passagens SIGEPA têm um GUID no lugar do número (1.292) e repetem códigos (305 linhas); 71 despesas de telefonia têm o código `0`; 4 de manutenção de escritório repetem um código. A `parcela`, sempre 0, não desempata.

## Conclusões para o ADR

1. **Fonte: nenhuma basta sozinha.** O arquivo anual tem o sinal correto do líquido (menos no auxílio-moradia), sai numa única requisição, traz também quem saiu da bancada e é atualizado diariamente. Mas não traz nenhuma passagem SIGEPA, e traz o CPF do deputado e o nome de passageiros, que teriam de ser descartados na ingestão. A API traz as passagens SIGEPA, mas inverte o sinal do líquido na maior parte das categorias, sem documentação, e só alcança os deputados da lista consultada. Decidir entre o arquivo mais a API só para as passagens SIGEPA, ou a API para tudo, com uma regra de sinal por categoria.
2. **`mes_ref` é a competência** (`ano` e `mes`), e não a data do documento: é o que os filtros da API e o arquivo usam, e a data falta em telefonia e auxílio-moradia.
3. **`mes_fechado`:** o critério de partida é o prazo da norma, 90 dias contados do fim do mês de competência, a confirmar com a segunda coleta. Consequência: o reprocessamento das despesas precisa cobrir pelo menos 4 meses, e o ADR-007 usa 3.
4. **O teste `valor_liquido >= 0` não vale como está:** há negativos legítimos (créditos de passagens). Avaliar no lugar dele um teste de que negativos só aparecem em categorias conhecidas e outro de consistência (`líquido = documento − glosa`, exceto documentos divididos). O auxílio-moradia precisa de uma regra própria, porque o sinal dele é o oposto do das demais categorias nas duas fontes.
5. **O total do mês soma o líquido**, nunca o valor do documento.
6. **CPF:** mascarar na ingestão, antes de gravar o Parquet, porque o bruto é publicado na release; inclusive o CPF dentro do nome de um MEI. **O site não deve linkar o comprovante das despesas com CPF**, porque a imagem mostra o CPF por inteiro (e, no exemplo, o endereço residencial da deputada). Decidir se também deixa de linkar os demais comprovantes, apontando para a página oficial de gastos do deputado na Câmara.
7. **Chave:** a `despesa_sk` precisa de mais campos que o `codDocumento`.
8. **Categorias:** um seed com as categorias normalizadas, mantendo a original, e um teste de dados para categoria nova não mapeada, como no ADR-007.
