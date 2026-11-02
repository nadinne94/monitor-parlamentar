# Spike: API de deputados da Câmara

- **Data:** 2026-11-02
- **Pergunta:** como a API entrega a lista de deputados de MG, e ela atende à `dim_parlamentar` do ADR-003?

## Endpoint

Lista:

```
GET https://dadosabertos.camara.leg.br/api/v2/deputados?siglaUf=MG&ordem=ASC&ordenarPor=nome
```

Detalhe de um deputado (o endereço vem no campo `uri` de cada item da lista):

```
GET https://dadosabertos.camara.leg.br/api/v2/deputados/{id}
```

Nenhuma das duas exige autenticação.

## Estrutura da resposta

A resposta tem duas chaves no topo: `dados` (lista de deputados) e `links` (navegação entre páginas).

```json
{
  "dados": [
    {
      "id": 74646,
      "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/74646",
      "nome": "Aécio Neves",
      "siglaPartido": "PSDB",
      "uriPartido": "https://dadosabertos.camara.leg.br/api/v2/partidos/36835",
      "siglaUf": "MG",
      "idLegislatura": 57,
      "urlFoto": "https://www.camara.leg.br/internet/deputado/bandep/74646.jpg",
      "email": "dep.aecioneves@camara.leg.br"
    }
  ],
  "links": [
    {"rel": "self", "href": "...deputados?ordem=ASC&ordenarPor=nome&siglaUf=MG"},
    {"rel": "first", "href": "...&pagina=1&itens=1000"},
    {"rel": "last", "href": "...&pagina=1&itens=1000"}
  ]
}
```

| Campo | Tipo | Observação |
|---|---|---|
| `id` | inteiro | Identificador do deputado na Câmara |
| `uri` | texto | Endereço do detalhe do deputado |
| `nome` | texto | Nome parlamentar (o nome usado no mandato, não o nome civil) |
| `siglaPartido` | texto | Partido atual |
| `uriPartido` | texto | Endereço do partido na API |
| `siglaUf` | texto | Sempre `MG` nesta consulta |
| `idLegislatura` | inteiro | `57` para todos |
| `urlFoto` | texto | Foto oficial |
| `email` | texto | Preenchido para todos os 53 nesta consulta |

### Respostas

**1. Quantos deputados de MG a consulta devolve?** 53, exatamente o número de cadeiras de Minas Gerais. A consulta devolve quem ocupa as cadeiras hoje, o que pode incluir suplentes em exercício (o detalhe informa isso no campo `condicaoEleitoral`).

**2. Quais campos cada deputado tem?** Nove, listados na tabela acima: dois inteiros (`id`, `idLegislatura`) e sete textos.

**3. Algum campo vem sempre nulo?** Não na lista: todos os campos vieram preenchidos para os 53. Uma issue antiga no repositório de dados abertos da Câmara relatava `email` sempre nulo, o que hoje não se confirma. Conclusão: a disponibilidade de campos **muda com o tempo**, e o modelo de validação deve tratar campos não essenciais como opcionais.

**4. Qual o valor de `idLegislatura`, e o que isso indica?** `57` para todos, a legislatura de 2023 a 2027. Sem o parâmetro `idLegislatura`, a API devolve os deputados **em exercício no momento da consulta**. Consequência importante: a partir de 1º de fevereiro de 2027, a mesma consulta passará a devolver a bancada da legislatura 58. Ver conclusões.

## Paginação

**5. O que muda em `links` com `&itens=10`?** A resposta passa a ter 10 deputados, e `links` ganha um quarto valor, `next`:

| `rel` | `href` (resumido) |
|---|---|
| `self` | `...&itens=10` |
| `next` | `...&pagina=2&itens=10` |
| `first` | `...&pagina=1&itens=10` |
| `last` | `...&pagina=6&itens=10` |

Com 53 deputados e 10 por página, são 6 páginas, e o `last` aponta para a página 6. Na primeira página não existe `previous`.

**6. Qual o máximo de `itens` por página?** Não foi possível determinar um limite:

- Com `itens=100` e com `itens=200`, vieram os 53 deputados de MG numa única página, sem erro, e os links refletem o valor pedido (`itens=100`, `itens=200`).
- Sem o parâmetro `itens`, os links indicam `itens=1000`: a API usou páginas de 1000 itens. Consultando **todos** os deputados, sem filtro de UF e sem `itens`, a lista inteira veio numa página só.
- Consultando todos os deputados com `itens=100`, vieram exatamente 100 por página, com `last` na página 6 (coerente com as 513 cadeiras da Câmara).

Como MG tem só 53 deputados, os testes com 100 e 200 não mostram se a API limitaria um valor alto numa consulta maior. Conclusão prática: **o cliente não deve depender do tamanho padrão nem de um máximo**. Ele deve pedir um valor explícito e seguro (`itens=100`) e seguir o `next`.

**Observação extra:** `siglaUf=` vazio não dá erro; o filtro é ignorado e a API devolve deputados de todos os estados. Um parâmetro mal preenchido no código passaria despercebido, trazendo dados de outros estados. A ingestão deve validar que todos os registros vieram com a UF pedida.

**7. Como saber que chegou à última página?** Sem `itens` (ou com `itens` maior que 53), os deputados de MG cabem numa única página: `first` e `last` apontam para a mesma URL (`pagina=1`) e não existe `next`. Com `itens=10`, a página 1 traz `next` apontando para a página 2, e `last` para a página 6. A regra para o cliente HTTP: **seguir o link `next` enquanto ele existir**; a ausência de `next` indica a última página. Essa regra funciona tanto para uma página quanto para várias, sem depender de calcular o número de páginas.

## Casos de borda

**8. UF inexistente (`siglaUf=XX`).** Não vem erro: a resposta tem a lista `dados` vazia, e `links` traz apenas `self` (sem `first` nem `last`). O navegador exibiu a resposta normalmente, o que indica status 200; o status exato será confirmado quando a resposta for gravada nos testes do passo 4.

Consequência: para a API, "nenhum resultado" é uma resposta válida, não um erro. Se a ingestão pedir uma UF errada (ou se a API passar por alguma falha que devolva lista vazia), nada vai acusar o problema automaticamente. Ver conclusões.

**Divergência entre lista e detalhe.** Para o mesmo deputado (id 74646), a lista traz `email` e `uriPartido` preenchidos, enquanto o `ultimoStatus` do detalhe traz os dois como `null` (o e-mail aparece dentro de `gabinete.email`). As duas visões da API não são totalmente consistentes, e cada campo deve ser lido de uma origem só.

## Lista x detalhe

**9. O que o detalhe tem a mais?** Exemplo do id 74646:

```json
{
  "dados": {
    "id": 74646,
    "nomeCivil": "AÉCIO NEVES DA CUNHA",
    "ultimoStatus": {
      "nome": "Aécio Neves",
      "siglaPartido": "PSDB",
      "idLegislatura": 57,
      "data": "2023-02-01",
      "nomeEleitoral": "Aécio Neves",
      "gabinete": {"nome": "20", "predio": "x", "sala": "20", "andar": null, "telefone": "3215-5964", "email": "dep.aecioneves@camara.leg.br"},
      "situacao": "Exercício",
      "condicaoEleitoral": "Titular",
      "descricaoStatus": null
    },
    "cpf": "(omitido nesta nota)",
    "sexo": "M",
    "urlWebsite": null,
    "redeSocial": [],
    "dataNascimento": "1960-03-10",
    "dataFalecimento": null,
    "ufNascimento": "MG",
    "municipioNascimento": "Belo Horizonte",
    "escolaridade": "Superior"
  }
}
```

Campos que só existem no detalhe: `nomeCivil`, `cpf`, `sexo`, `dataNascimento`, `dataFalecimento`, `ufNascimento`, `municipioNascimento`, `escolaridade`, `urlWebsite`, `redeSocial` e, dentro de `ultimoStatus`, `situacao` (ex.: "Exercício"), `condicaoEleitoral` (ex.: "Titular"), `data` (início do status atual), `nomeEleitoral` e `gabinete`.

**Atenção (LGPD):** o detalhe expõe o **CPF** do deputado. O projeto não precisa desse dado. Ele deve ser descartado já na ingestão, antes de qualquer gravação, e nunca chegar ao Parquet, ao banco ou ao site. Isso vale especialmente para o futuro dataset público do Hugging Face (ADR-005).

## Comparação com o contrato (ADR-003)

**10. Quais colunas da `dim_parlamentar` cada origem atende?**

| Coluna do contrato | Origem | Campo da API |
|---|---|---|
| `parlamentar_sk` | Calculada | hash de `fonte` + `id_fonte` |
| `fonte` | Constante | `camara_api` |
| `id_fonte` | Lista | `id` |
| `nome_parlamentar` | Lista | `nome` |
| `nome_civil` | **Só detalhe** | `nomeCivil` |
| `casa` | Constante | `camara_deputados` |
| `esfera` | Constante | `federal` |
| `uf` | Lista | `siglaUf` |
| `municipio` | Nenhuma | Nulo por definição na esfera federal |
| `partido_atual` | Lista | `siglaPartido` |
| `url_foto` | Lista | `urlFoto` |
| `em_exercicio` | Lista (indireto) ou detalhe | A lista padrão só devolve quem está em exercício; o detalhe informa explicitamente em `ultimoStatus.situacao` |

Resumo: a **lista atende a todas as colunas, exceto `nome_civil`**, que só existe no detalhe. `em_exercicio` pode ser deduzido da própria consulta, enquanto ela for feita sem o parâmetro `idLegislatura`. `municipio` é nulo para deputados federais, como o ADR-003 já previa.

O detalhe ainda oferece um dado que o contrato não tem e que será útil: `condicaoEleitoral` (titular ou suplente), relevante para a virada de legislatura (roadmap, Incremento 6).

## Conclusões para o Incremento 1

1. **Paginação:** o cliente HTTP deve seguir o link `next` até ele deixar de existir, e não calcular páginas. Funciona para uma página (deputados de MG) e para muitas (proposições, despesas, nos incrementos seguintes).
2. **Validação tolerante:** campos não essenciais, como `email`, devem ser opcionais no modelo Pydantic. A disponibilidade deles já mudou no passado.
3. **Decisão pendente: lista apenas ou lista e detalhe?**
   - **Opção A, só a lista (1 requisição):** atende a todas as colunas, exceto `nome_civil`, que passa a ser anulável no contrato e é preenchida num incremento futuro.
   - **Opção B, lista e detalhe (54 requisições):** preenche `nome_civil` e traz `situacao` e `condicaoEleitoral`, ao custo de 53 chamadas extras, cuidado com o volume de requisições à API e o descarte obrigatório do CPF.
4. **Legislatura:** a consulta sem `idLegislatura` devolve sempre a bancada atual. A ingestão deve aceitar a legislatura como parâmetro (57 para testes com dados de 2026; 58 a partir de fevereiro de 2027), em vez de depender do comportamento padrão da API, que muda sozinho em 1º de fevereiro.
5. **CPF:** se o detalhe for usado (opção B), o descarte do CPF na ingestão é obrigatório e precisa de um teste próprio.
6. **Tamanho da página:** o cliente pede sempre um valor explícito (`itens=100`) em vez de depender do padrão da API, que nesta consulta foi de 1000 itens e pode mudar.
7. **Lista vazia:** o cliente HTTP genérico trata lista vazia como resposta válida, porque em outros endpoints ela é normal (um mês sem votações, por exemplo). Quem decide se o vazio é um problema é a ingestão de cada recurso: para os deputados de MG, uma lista vazia é sempre uma anomalia e deve falhar a execução.
8. **Filtro ignorado:** como `siglaUf` vazio é ignorado sem erro, a ingestão valida que todos os registros recebidos têm a UF pedida. Um teste de dados no dbt (`accepted_values` em `uf`) reforça essa garantia na transformação.
