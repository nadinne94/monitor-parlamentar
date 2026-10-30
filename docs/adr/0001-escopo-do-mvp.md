# ADR-001: Escopo do MVP

- **Status:** Aceito
- **Data:** 2026-10-27
- **Decisora:** Nadinne

## Contexto

O objetivo de longo prazo do projeto é permitir que qualquer cidadão acompanhe, mês a mês, a atuação de parlamentares e políticos municipais: presença, votos, proposições, emendas e uso de verbas.

Essa visão completa envolve várias esferas (federal, estadual, municipal), várias casas (Câmara, Senado, câmaras municipais) e fontes de dados com qualidade e formatos muito diferentes. É um volume de trabalho incompatível com uma desenvolvedora solo e recursos gratuitos, se for atacado de uma vez.

O projeto adota desenvolvimento incremental em fatias verticais: cada incremento atravessa o sistema inteiro (ingestão → transformação → site publicado) para um conjunto pequeno de dados. Para isso, é preciso definir um primeiro escopo pequeno, útil por si só e que valide a arquitetura.

Fatores considerados:

- A API de Dados Abertos da Câmara dos Deputados é a fonte mais madura e já é conhecida (projeto anterior `projeto_api_dados_abertos_camara`).
- Os deputados eleitos em 2026 tomam posse em 1º de fevereiro de 2027. Janeiro é recesso, ainda na legislatura anterior.
- Fontes municipais têm disponibilidade incerta e dependem de investigação prévia (spike).

## Decisão

O MVP responde a uma única pergunta:

> **"O que o deputado federal de Minas Gerais que eu escolhi fez neste mês?"**

### Dentro do escopo

- **Casa:** Câmara dos Deputados.
- **Recorte:** bancada de Minas Gerais.
- **Granularidade:** mensal, por parlamentar.
- **Entrega:** uma página por deputado com o relatório do mês e navegação entre meses.
- **Métricas (4):**
  1. **Proposições:** proposições de autoria ou coautoria do deputado apresentadas no mês.
  2. **Presença:** participação em sessões deliberativas do plenário no mês.
  3. **Votos nominais:** votos registrados pelo deputado em votações nominais do plenário no mês.
  4. **Despesas da cota parlamentar (CEAP):** valores declarados no mês, por categoria de despesa.
- **Período:** a primeira competência oficial é **fevereiro de 2027**. O sistema é construído e testado com dados de 2026 (legislatura atual).

### Fora do escopo (incrementos futuros)

- Senado Federal.
- Câmaras municipais e prefeitura.
- Emendas parlamentares (Portal da Transparência).
- Deputados de outros estados.
- Rankings, notas ou comparações entre parlamentares.
- Votações em comissões.

## Alternativas consideradas

**Começar pelo município.** Rejeitada para o MVP. Câmaras municipais raramente oferecem API, e a qualidade dos portais de transparência é heterogênea. O risco de travar na coleta, em vez de exercitar as práticas de engenharia, é alto. Será avaliada por um spike separado (verificar se a câmara usa o SAPL do Interlegis, que expõe API REST).

**Todos os 513 deputados desde o início.** Rejeitada. O recorte por estado não muda a arquitetura (é um filtro) e reduz volume, tempo de execução no CI e esforço de validação manual. Ampliar para todos os estados é um incremento de baixo custo depois.

**Três métricas (sem proposições).** Rejeitada. Proposições são uma das atividades mais visíveis de um parlamentar e completam o retrato do mês junto com presença, votos e gastos.

**Incluir emendas no MVP.** Rejeitada. Emendas vêm de outra fonte (Portal da Transparência, que exige chave de API) e têm ciclo orçamentário anual, não mensal, o que complica a leitura "o que fez este mês".

## Consequências

**Positivas**

- Escopo pequeno o suficiente para ter o primeiro incremento publicado em poucas semanas.
- Valida a arquitetura completa (ingestão, contrato canônico, site estático, pipeline agendado) com uma fonte confiável.
- Cada métrica é uma fatia vertical independente, que pode ser entregue e publicada separadamente.

**Negativas / riscos**

- O usuário de outros estados ou interessado em senadores não é atendido no MVP.
- Reaproveitar a mesma API do projeto anterior reduz a novidade técnica na coleta. A diferenciação está no produto (relatório mensal por parlamentar) e nas práticas (testes desde o início, CI/CD, incrementos).

**Pontos em aberto (a resolver antes ou durante a implementação de cada métrica)**

- **Proposições:** definir quais tipos contam. Incluir só proposições legislativas (PL, PLP, PEC, PDL) ou também requerimentos, indicações etc.? Requerimentos são numerosos e podem inflar a contagem. Tratar autoria e coautoria de forma separada ou somada.
- **Presença:** confirmar na API qual endpoint representa melhor a presença em plenário e como aparecem ausências justificadas (missão oficial, licença). A métrica precisa distinguir "ausente" de "ausência justificada" para não distorcer a leitura.
- **Votos nominais:** decidir como exibir "obstrução", "abstenção" e "art. 17" (presidente não vota).
- **CEAP:** as despesas podem ser lançadas com atraso. Definir se o mês é o da emissão do documento ou o da competência informada, e quando um mês é considerado "fechado".
- **Virada de legislatura:** tratar deputados que saem, entram, assumem como suplentes ou mudam de partido em fevereiro de 2027.

Cada ponto em aberto deve ser resolvido em ADR próprio ou registrado na página de metodologia do site.
