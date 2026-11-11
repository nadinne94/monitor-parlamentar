# Spike S5: API de votações da Câmara

- **Data:** 2026-11-08
- **Pergunta:** como obter os votos da bancada de MG nas votações nominais do Plenário em cada mês, e o que os dados mostram sobre tipos de votação, valores de voto, ausências e contexto?

## Lista de votações

```
GET https://dadosabertos.camara.leg.br/api/v2/votacoes?idOrgao=180&dataInicio=...&dataFim=...
```

- O Plenário é o órgão de id **180**.
- **Outubro de 2026: 39 votações**, numa única página (`itens=100`).
- **Limite de período:** um intervalo de 4 meses (julho a outubro) funcionou, em 4 páginas de 100. Diferente das proposições, não apareceu o limite de 3 meses.
- **O `id` é um texto**, no formato `2611719-7` (o número da proposição, um hífen e um sequencial). Na ingestão, é uma string.
- **Campos de cada item:** `id`, `uri`, `data`, `dataHoraRegistro`, `siglaOrgao`, `uriOrgao`, `uriEvento`, `proposicaoObjeto` (só em parte dos itens, como `REQ 1634/2026`), `uriProposicaoObjeto`, `descricao` e `aprovacao` (1 ou 0).
- **O campo `aprovacao` pode faltar:** a votação `2637101-44`, de descrição "Mantido o texto.", veio sem ele. É a resposta típica de um destaque.

## Votações nominais e simbólicas

- **A lista não tem um campo que diga se a votação é nominal.**
- A votação `2611719-7` (urgência aprovada "por unanimidade") veio com a lista de votos **vazia**: foi simbólica, sem registro individual.
- **Só 3 das 39 votações de outubro trazem placar na descrição** e têm votos registrados:

| Votação | O que foi votado | Resultado |
|---|---|---|
| `2635476-23` | Requerimento | Rejeitado (Sim 11, Não 387) |
| `2635476-36` | Subemenda substitutiva global ao PLP 186/2026 | Aprovada (Sim 461, Não 4) |
| `2236186-60` | Subemenda substitutiva ao PLP 281/2019 | Rejeitada (Sim 252, Não 176) |

- Em setembro, a lista de quatro meses mostra outras votações com placar, inclusive com **abstenções** (por exemplo, `Sim: 346; Não: 46; Abstenção: 3`).
- **A forma confiável de saber se uma votação foi nominal é consultar os votos:** lista vazia, simbólica; lista preenchida, nominal. O placar na descrição é só um indício.

## Votos

```
GET /votacoes/{id}/votos
```

- Cada voto traz `tipoVoto`, `dataRegistroVoto` e o deputado (`id`, `uri`, `nome`, `siglaPartido`, `uriPartido`, `siglaUf`, `idLegislatura`, `urlFoto`, `email`). **A UF vem em cada voto**, o que permite filtrar a bancada de MG.
- O `email` falta em alguns deputados: é um campo opcional.
- **Valores observados no tipo de voto:** `Sim`, `Não` e `Artigo 17`. O `Artigo 17` aparece para o presidente da Câmara, que, pelo Regimento Interno, só vota em caso de empate: não é um voto de posição. `Abstenção` aparece nos placares de setembro. `Obstrução` não apareceu na amostra.

## Ausências

- **A lista de votos traz apenas quem registrou voto.** Um deputado que não votou simplesmente não aparece.
- Não existe na lista um valor para "ausente". A ausência precisa ser **inferida**: um deputado em exercício que não está na lista de uma votação nominal não registrou voto nela.
- Não registrar voto **não é o mesmo que faltar**: o deputado pode estar em licença, em missão oficial ou em outra atividade da Casa. A API, nesta consulta, não diz o motivo.
- A contagem exata de quantos dos 53 deputados de MG aparecem em cada votação fica para a implementação, com o DuckDB.

## Contexto da votação

```
GET /votacoes/{id}
```

- O detalhe traz as **proposições afetadas**. Exemplo: a votação `2611719-7` (urgência do REQ 1634/2026) aponta para o **PL 1381/2026, "Institui o Dia Nacional do Ceará e do Cearense e da Cearense"**.
- A **descrição** diz o que foi votado, mas na linguagem do processo legislativo: subemenda substitutiva global, redação final, apreciação preliminar do parecer da comissão mista, destaque ("Mantido o texto").
- **O resultado não pode ser deduzido do placar.** A votação `2236186-60` teve mais votos Sim (252) do que Não (176) e foi **rejeitada**: por ser um projeto de lei complementar, precisava de maioria absoluta da Câmara (257 votos). O resultado correto vem do campo `aprovacao` e da descrição, nunca de uma comparação entre Sim e Não.

## Orientações dos partidos

```
GET /votacoes/{id}/orientacoes
```

- Cada orientação traz o tipo de liderança (`B` para bloco, `P` para partido), a sigla, o código e a orientação.
- Na votação `2236186-60`, orientaram blocos (Maioria, Minoria, Governo, Oposição, o bloco União/PP/PSD...), **federações** (Fdr PSOL-REDE, Fdr PT-PCdoB-PV) e partidos.
- **Algumas lideranças aparecem sem orientação** registrada na resposta.
- Comparar o voto de um deputado com a orientação do seu partido **não é direto**: muitos partidos orientam por meio do bloco ou da federação, e seria preciso saber a que bloco e federação cada partido pertence em cada data.

## Volume

- Uma consulta à lista por mês (uma ou duas páginas).
- Uma consulta aos votos de cada votação, para saber quais foram nominais: cerca de 40 a 100 requisições por mês, um volume parecido com o das proposições.
- As respostas de votos nominais são grandes (cerca de 460 registros cada), mas são poucas por mês.

## Conclusões para o ADR-008

1. **Contar só as votações nominais do Plenário.** As simbólicas não têm voto individual, e as das comissões ficam para depois.
2. **Identificar as nominais pela lista de votos**, e não pelo texto da descrição.
3. **Vocabulário do voto:** `sim`, `nao`, `abstencao`, `obstrucao` e `artigo_17` (presidente da sessão). A ausência de registro é um estado à parte, inferido, e deve ser exibida como "sem voto registrado", nunca como "faltou".
4. **O resultado vem do campo `aprovacao`**, nunca do placar, porque o quórum exigido muda com o tipo de proposição.
5. **Exibir a descrição oficial e a proposição afetada**, com link para a fonte. Traduzir a votação para linguagem simples continua no backlog.
6. **A comparação com a orientação partidária fica para depois do MVP**, por depender de blocos e federações.
7. **Decisão em aberto:** como mostrar um número tão pequeno de votações nominais por mês (3 em outubro) sem que o visitante leia isso como pouca atividade.

## Confirmação com a coleta real (outubro de 2026)

- 39 votações no Plenário: 36 simbólicas e 3 nominais, como a amostra indicava.
- Cada lista de votos tem um registro a mais que o placar oficial: o `Artigo 17` do presidente da sessão, que não entra no placar.
- Valores de voto em outubro: `Sim`, `Não` e `Artigo 17`.
- Deputados de MG com voto registrado: 41, 36 e 48 nas três votações nominais.
- Cada votação nominal afetou exatamente uma proposição. O requerimento rejeitado (`2635476-23`) afeta o PLP 186/2026, o que permite explicar do que ele tratava.
