# Spike S3: API de proposições da Câmara

- **Data:** 2026-11-07
- **Pergunta:** como obter as proposições apresentadas pelos deputados de MG em cada mês, e o que os dados mostram sobre tipos e autoria?

## Consulta

Endpoint da lista:

```
GET https://dadosabertos.camara.leg.br/api/v2/proposicoes
```

Parâmetros testados:

| Parâmetro | Resultado |
|---|---|
| `idDeputadoAutor=74646` | Funciona. Sem filtro de data, devolveu proposições de 1991 a 1999 (22 páginas). |
| `siglaUfAutor=MG` | Funciona, inclusive combinado com as datas. |
| `siglaPartidoAutor=PL` | Funciona (201 páginas, sem filtro de data). |
| `dataApresentacaoInicio` e `dataApresentacaoFim` | Funcionam, com um limite: **o intervalo não pode passar de 3 meses**. Um ano inteiro devolve erro 400: "A diferença entre as datas não pode ser maior que 3 meses". |

**Comportamento sem datas:** sem nenhum parâmetro, a API devolveu 991 páginas, muito menos que o total histórico, e a primeira proposição (PL 1156/2003) tinha uma tramitação recente. Tudo indica um filtro padrão por tramitação recente, que não está claro. Com o `idDeputadoAutor`, esse recorte não aconteceu. Conclusão: a ingestão nunca deve depender do comportamento padrão e precisa sempre passar as datas.

**O que cada item da lista traz:** `id`, `uri`, `siglaTipo`, `codTipo`, `numero`, `ano`, `ementa` e a **data de apresentação** (`dataApresentacao`). O mês de cada proposição sai do próprio dado, sem consultar o detalhe.

**O detalhe** (`/proposicoes/{id}`) traz mais: situação atual, último despacho, link do inteiro teor, palavras-chave e ementa detalhada. Os endpoints `/relacionadas`, `/tramitacoes` e `/votacoes` também existem.

## Volume

- `idDeputadoAutor=74646` em outubro de 2026: nenhuma proposição.
- `siglaUfAutor=MG` em outubro de 2026: **88 itens**, numa única página (`itens=100`).

## Tipos

Itens de outubro de 2026 com `siglaUfAutor=MG`, agrupados:

| Grupo | Tipos (quantidade) | Total |
|---|---|---|
| Projetos | PL (23), PLP (2), PDL (1), PRC (4) | 30 |
| Requerimentos e indicações | REQ (17), RIC (6), INC (3) | 26 |
| Documentos de relatoria e tramitação | PRL (10), SBT (5), RDF (5), EMP (2), SBR (1) | 23 |
| Requerimentos de procedimento em plenário | RPD (7), REC (1) | 8 |
| Outros | PROC (1) | 1 |
| **Total** | | **88** |

Significado das siglas (de `/referencias/proposicoes/siglaTipo`): PL, projeto de lei; PLP, projeto de lei complementar; PDL, projeto de decreto legislativo; PRC, projeto de resolução; REQ, requerimento; RIC, requerimento de informação; INC, indicação; PRL, parecer do relator; SBT, substitutivo; RDF, redação final; EMP, emenda de plenário; SBR, subemenda de relator; RPD, requerimento procedimental; REC, recurso; PROC, processo interno.

**Observações:**

- **Um quarto dos itens são documentos de relatoria** (pareceres, substitutivos, redações finais). Eles aparecem porque, para a API, o relator é o autor do parecer. É uma atividade diferente de apresentar uma proposição.
- **Requerimentos e indicações quase empatam com os projetos.** Contar tudo junto daria o mesmo peso a um pedido de audiência pública e a um projeto de lei.
- **A sigla REQ tem dezenas de `codTipo` diferentes**, e o `codTipo` vem em cada item da lista. Exemplos em outubro: 294 (audiência pública), 355 (voto de pesar), 392 (urgência, art. 155 do RICD), 313 (inclusão ou retirada de assinatura), 1017 (requerimento de informação enviado pela comissão), 293 (sessão solene). Os requerimentos podem ser classificados sem consultar o detalhe.

## Autoria

Endpoint: `GET /proposicoes/{id}/autores`. Cada autor traz `nome`, `codTipo`, `tipo`, `ordemAssinatura` e `proponente`.

| Proposição | Tipo | Autores | Observação |
|---|---|---|---|
| 2648590 | PL | 1 (Paulo Guedes) | `proponente` 1, `ordemAssinatura` 1 |
| 2647384 | PL | 1 (Rogério Correia) | `proponente` 1, `ordemAssinatura` 1 |
| 2647401 | PRL | 1 (Lafayette de Andrada) | O relator aparece como autor do parecer |
| 2649509 | RDF | 1 (Patrus Ananias) | O autor da redação final é um deputado, não a comissão |
| 117992 | PL | 1 (Rogério Silva) | Proposição de 2003, mesmo formato |

Em todos, o autor tem `tipo` "Deputado(a)" (`codTipo` 10000).

**Coautoria:** nenhum dos exemplos teve mais de um autor, mas ela existe e **pode ser acrescentada depois**: o REQ 2648642 (`codTipo` 313) pede "a inclusão de coautoria deputados subscritores do presente requerimento ao Projeto de Lei nº 2.976, de 2026", e o PL 1156/2003 tem um requerimento semelhante entre as relacionadas. A lista de autores de uma proposição **pode mudar com o tempo**.

**Não respondido neste spike:** se o `siglaUfAutor=MG` traz proposições em que um deputado de MG é apenas coautor.

## Conclusões para o ADR-007

1. **Consulta mensal com datas explícitas.** Um mês por consulta respeita o limite de 3 meses. Uma carga histórica precisa ser feita mês a mês.
2. **Uma consulta por mês para a bancada inteira** (`siglaUfAutor=MG`) é viável: 88 itens, numa página. Para atribuir cada proposição a cada deputado, e tratar a coautoria, a ingestão consulta os autores de cada item: cerca de 90 requisições por mês, um volume que o cliente HTTP atual suporta.
3. **Os itens precisam ser classificados em grupos**, pelo `siglaTipo` e, para os requerimentos, pelo `codTipo`. Os documentos de relatoria e os requerimentos procedimentais não são "proposições apresentadas" e não devem entrar nessa contagem.
4. **A autoria pode mudar depois da apresentação** (coautoria incluída por requerimento). Reprocessar os meses recentes, como o ADR-002 já previa para as despesas, mantém a autoria atualizada.
5. **Decisões em aberto para o ADR-007:** quais grupos contar e como exibi-los; se a coautoria conta junto com a autoria principal ou separada; se os projetos de resolução (PRC) entram no grupo dos projetos; e se vale investigar, na implementação, se o filtro por UF inclui os coautores.

## Atualização com a primeira coleta completa (passo 8, outubro de 2026)

- **Coautoria:** 253 autorias para 87 proposições; a maior teve 65 assinaturas. A coautoria é comum, o que confirma a separação entre autoria e coautoria do ADR-007.
- **Proposição sem autores:** o PROC 2648534 (representação por quebra de decoro) veio sem nenhum autor na API. Nem toda proposição tem autor listado.
- **Autores que não são deputados:** nenhum em outubro.
- **O filtro por UF inclui coautorias:** 7 proposições têm o primeiro autor fora da bancada de MG e vieram na consulta por terem coautores de MG. A consulta por UF é suficiente, e a alternativa por deputado não é necessária.
