# ADR-008: Votações nominais

- **Status:** Aceito
- **Data:** 2026-11-08
- **Decisora:** Nadinne
- **Relacionado:** [ADR-001](0001-escopo-do-mvp.md), [ADR-003](0003-contrato-canonico.md), spike S5 (`docs/spikes/s5-api-votacoes.md`)

## Contexto

O ADR-001 definiu os votos nominais como uma das quatro métricas do MVP. O spike S5 mostrou que:

- Em outubro de 2026, o Plenário fez 39 votações, e só 3 foram nominais. As demais foram simbólicas, sem registro de como cada deputado votou.
- A lista de votações não informa se uma votação é nominal. Só a lista de votos revela isso: vazia nas simbólicas, preenchida nas nominais.
- A lista de votos traz apenas quem registrou voto. Não há um valor para "ausente", e a API não informa o motivo de um deputado não ter votado.
- Os valores de voto incluem `Artigo 17`, usado para o presidente da Câmara, que só vota em caso de empate.
- O resultado não pode ser deduzido do placar: uma votação com 252 votos Sim e 176 Não foi rejeitada, porque exigia maioria absoluta.
- As orientações partidárias são dadas por blocos, federações e partidos, e várias lideranças aparecem sem orientação.

Votações são o dado mais sensível do projeto: um voto mal apresentado pode ser injusto com uma pessoa real.

## Decisão

### 1. Quais votações entram

- Só as votações **nominais do Plenário** (órgão 180). Uma votação é nominal quando a sua lista de votos não está vazia.
- As votações simbólicas são coletadas e guardadas, mas não geram votos individuais.
- As votações das comissões ficam fora do MVP.

### 2. O modelo

- **`dim_votacao`**: uma linha por votação nominal, com a data, a descrição oficial, o resultado (do campo `aprovacao` da API), o placar e a proposição afetada (sigla, número, ano e ementa).
- **`fato_voto`**: uma linha por **votação nominal × parlamentar da bancada**, com o voto.
- As duas são novas tabelas do contrato canônico, uma mudança compatível pela seção 5 do ADR-003. O contrato passa à versão 1.2.0.

### 3. O vocabulário do voto

| Valor | Significado |
|---|---|
| `sim` | Votou Sim |
| `nao` | Votou Não |
| `abstencao` | Registrou abstenção |
| `obstrucao` | Registrou obstrução |
| `artigo_17` | Presidiu a sessão e, pelo Regimento, só votaria em caso de empate |
| `sem_registro` | Estava na bancada, mas não registrou voto nessa votação |

- `sem_registro` é **inferido**: o parlamentar está na `dim_parlamentar`, mas não aparece na lista de votos. O site o exibe como "sem voto registrado", **nunca** como "faltou" ou "ausente", porque a API não informa o motivo.
- Um valor de voto desconhecido faz um teste de dados falhar, para ser analisado antes de entrar no site.

### 4. O resultado

- O resultado vem **sempre** do campo `aprovacao` da API e da descrição oficial, **nunca** de uma comparação entre o número de votos Sim e Não.
- Uma votação sem o campo `aprovacao` (como a manutenção de um texto destacado) é exibida com a descrição oficial, sem um resultado calculado.

### 5. O que o site mostra

- Para cada mês, uma frase de contexto: quantas votações o Plenário fez e quantas foram nominais. Isso evita que um número pequeno de votações nominais seja lido como pouca atividade.
- Para cada votação nominal: a data, a descrição oficial, a proposição afetada com a ementa, o resultado e o voto do deputado, com link para a votação na fonte oficial.
- Sem percentuais, sem rankings e sem comparação entre deputados.

### 6. Fora do MVP

- A comparação do voto com a orientação do partido, que depende de saber a que bloco e federação cada partido pertencia em cada data.
- A explicação das votações em linguagem simples (já no backlog).

### 7. Coleta

- Uma consulta por mês à lista de votações do Plenário, com as datas explícitas.
- Uma consulta aos votos de cada votação, para identificar as nominais.
- Uma consulta ao detalhe de cada votação nominal, para obter a proposição afetada.
- Os mesmos últimos 3 meses de reprocessamento do ADR-007.

## Alternativas consideradas

**Contar as votações simbólicas como votos.** Rejeitada: não há registro individual, e atribuir a um deputado o resultado de uma votação simbólica seria afirmar algo que a fonte não diz.

**Exibir "ausente" para quem não votou.** Rejeitada: a API não informa o motivo, e "ausente" sugere uma falta que pode não ter acontecido.

**Não registrar quem não votou.** Rejeitada: o visitante veria só as votações em que o deputado votou, sem saber das outras. Registrar `sem_registro` explicitamente segue o princípio do ADR-003 de que nulo é diferente de zero.

**Calcular o resultado pelo placar.** Rejeitada: o quórum exigido muda com o tipo de proposição, e o cálculo erraria.

**Incluir a orientação partidária já no MVP.** Adiada: exige uma tabela de blocos e federações por data, que a API não entrega de forma direta.

## Consequências

**Positivas**
- O site mostra apenas o que a fonte registra, com o contexto necessário para não induzir conclusões erradas.
- O modelo dimensional separa os dados da votação (`dim_votacao`) dos votos (`fato_voto`), sem repetir a descrição em cada linha.

**Negativas / riscos**
- `sem_registro` usa a bancada **atual**. Um deputado que entrou na bancada depois de uma votação apareceria como "sem voto registrado" nela. O histórico de mandatos do Incremento 6 resolve isso; até lá, o risco é baixo nos últimos 3 meses.
- A descrição oficial continua na linguagem do processo legislativo.
- Os votos de uma votação nominal são grandes (cerca de 460 registros), mas são poucas votações nominais por mês.
