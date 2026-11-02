# ADR-005: Adiar a persistência dos dados brutos no Hugging Face

- **Status:** Aceito
- **Data:** 2026-11-02
- **Decisora:** Nadinne
- **Altera:** a decisão sobre persistência dos dados brutos no [ADR-002](0002-stack-tecnologica.md)

## Contexto

O ADR-002 definiu o Hugging Face Datasets como local de persistência dos dados brutos entre
execuções do pipeline, e o roadmap previa validar essa escolha (spike S2) antes do Incremento 1.

Com o Incremento 0 concluído, a necessidade foi reavaliada:

- No Incremento 1, a única fonte é a lista de deputados de MG, que a API devolve completa a
  cada consulta. O pipeline pode buscá-la de novo em cada execução, em poucos segundos.
- A persistência resolve um problema específico: dados históricos que mudam ou deixam de estar
  disponíveis na API. Esse problema aparece com as despesas da cota parlamentar (Incremento 4),
  lançadas com atraso e sujeitas a correções.
- Implementar a persistência agora exige conta, token, segredo no GitHub e uma nova dependência,
  sem benefício para os dados deste incremento.

## Decisão

- A persistência dos dados brutos é adiada para antes do Incremento 4.
- O spike S2 passa a ser pré-requisito do Incremento 4, e não do Incremento 1.
- Até lá, cada execução do pipeline busca os dados na API e grava os arquivos brutos apenas
  localmente, na pasta `data/`, ignorada pelo Git.
- A escolha do Hugging Face como destino continua válida e será confirmada ou revista pelo spike S2.

## Alternativas consideradas

**Manter o plano original (spike S2 antes do Incremento 1).** Rejeitada: adiciona complexidade
sem resolver nenhum problema dos dados deste incremento.

**Abandonar a persistência.** Rejeitada: o histórico das despesas exigirá guardar os snapshots
brutos, e o ADR-002 continua correto quanto a essa necessidade.

## Consequências

**Positivas**
- O Incremento 1 fica concentrado no caminho dos dados reais, da API ao site.
- Menos peças para configurar e manter até que sejam necessárias.

**Negativas / riscos**
- Até o Incremento 4, cada execução depende da disponibilidade da API da Câmara. Se ela estiver
  fora do ar, o deploy falha e o site publicado anteriormente continua no ar, sem atualização.
- Não haverá histórico dos dados brutos coletados antes do Incremento 4. Aceitável, porque a API
  mantém o histórico dos dados deste período.
