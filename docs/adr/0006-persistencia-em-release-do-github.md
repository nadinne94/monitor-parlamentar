# ADR-006: Persistência dos dados brutos em release do GitHub

- **Status:** Aceito
- **Data:** 2026-11-06
- **Decisora:** Nadinne
- **Substitui:** o [ADR-005](0005-adiar-persistencia-dados-brutos.md)
- **Altera:** a escolha do destino dos dados brutos no [ADR-002](0002-stack-tecnologica.md)

## Contexto

O ADR-005 adiou a persistência dos dados brutos para antes do Incremento 4, partindo da premissa
de que cada execução do pipeline poderia buscar todos os dados na API em poucos segundos.
Ele registrou como risco que, com a API fora do ar, o deploy falharia.

Entre 03 e 05/11/2026, o risco se materializou:

- A API da Câmara respondeu com erro 504 em várias ocasiões.
- Em 05/11/2026, ficou indisponível por mais de meia hora seguida. O deploy da versão 0.1.0 falhou
  e o site continuou desatualizado até a API voltar, mesmo sem nenhuma relação entre a mudança de
  código e os dados.

O cliente HTTP passou a fazer mais tentativas e a respeitar o cabeçalho `retry-after`, o que
resolve as falhas curtas, mas não as longas. Para estas, o deploy precisa de uma fonte de dados
que não dependa da API naquele instante.

O spike S2 (`docs/spikes/s2-persistencia.md`) comparou duas formas de guardar os dados brutos:
anexos de uma release do GitHub e um dataset no Hugging Face.

## Decisão

### 1. Destino: uma release técnica do GitHub

Os dados brutos são guardados como anexos de uma release chamada `dados-brutos`, marcada como
pre-release para não ser confundida com as versões do projeto.

Motivos, a partir do spike S2:

- Não exige conta nova, segredo cadastrado nem dependência nova: o GitHub Actions usa um token
  criado a cada execução, que expira sozinho, e a ferramenta `gh` já vem instalada.
- O ciclo completo de envio e download pelo Actions levou 13 segundos.
- Os arquivos podem ser baixados publicamente, sem login.

### 2. Convenção de nomes

As releases não têm pastas, então o nome do arquivo identifica a fonte, a tabela e a data:

- `<fonte>__<tabela>.parquet`: a coleta mais recente bem-sucedida (ex.: `camara_api__deputados.parquet`).
- `<fonte>__<tabela>__<AAAA-MM-DD>.parquet`: uma cópia por dia de coleta, em UTC, que forma o
  histórico (ex.: `camara_api__deputados__2026-11-06.parquet`). Uma segunda coleta no mesmo dia
  substitui a primeira.

### 3. O fluxo do pipeline

1. A ingestão tenta coletar os dados na API.
2. **Se der certo**, os arquivos são gravados localmente, como hoje, e enviados para a release:
   a cópia datada e a "mais recente".
3. **Se a API falhar** (erro HTTP ou de rede, depois de esgotadas as novas tentativas, ou conteúdo
   sem sentido), o pipeline baixa a cópia "mais recente" da release e continua a partir dela.
4. **Se não houver cópia na release**, ou se o erro for de configuração do próprio projeto, o
   pipeline falha, como hoje.
5. O site informa a data da coleta usada, para que o visitante saiba quando os dados foram obtidos.

Coerente com o princípio do ADR-002 de que nenhuma lógica roda só na nuvem, o envio e a recuperação
são feitos pela CLI `monitor`, com testes, e não por passos escritos apenas no workflow.

### 4. O Hugging Face

Deixa de ser o destino operacional. Continua como opção para um objetivo diferente, a avaliar no
futuro: publicar os dados tratados (os marts) como um dataset aberto e documentado.

## Alternativas consideradas

**Dataset no Hugging Face (escolha original do ADR-002).** Rejeitada como armazenamento operacional.
Oferece histórico nativo e uma página própria, mas exige conta, token de escrita guardado em
GitHub Secrets e uma dependência nova. Durante o spike, um token foi exposto acidentalmente e
precisou ser revogado, o que reforçou a vantagem de não ter segredo para gerenciar.

**Manter o ADR-005 (sem persistência até o Incremento 4).** Rejeitada: a premissa dele não se
sustentou, e cada queda da API impediria qualquer publicação, inclusive de mudanças só de código.

**Commitar os dados no repositório, artefatos ou cache do Actions.** Rejeitadas no spike S2:
inflam o histórico do Git, expiram ou são apagados sem aviso.

## Consequências

**Positivas**
- Uma queda da API deixa de impedir o deploy: o site é gerado com a última coleta bem-sucedida.
- O histórico diário das coletas começa a existir, o que vai ser necessário quando as despesas
  da cota parlamentar, corrigidas depois de lançadas, entrarem no projeto.
- Nenhum segredo a gerenciar.

**Negativas / riscos**
- O workflow de deploy passa a precisar de permissão de escrita no repositório
  (`contents: write`) para anexar arquivos à release. A permissão fica restrita ao job que precisa dela.
- O histórico depende da convenção de nomes, sem versionamento nativo.
- A release acumula um arquivo por fonte, tabela e dia. Com arquivos de poucos KB, não é um
  problema hoje; uma política de retenção pode ser necessária no futuro.
- O site pode exibir dados de alguns dias atrás durante uma queda longa. A data da coleta
  visível no site torna isso transparente.
