# Spike S2: persistência dos dados brutos

- **Data:** 05/11/2026
- **Pergunta:** onde guardar os arquivos brutos de cada coleta, para o deploy usar a última coleta bem-sucedida quando a API estiver fora do ar?
- **Motivação:** quedas longas da API da Câmara (ver roadmap, Incremento 2, e o desvio registrado no Incremento 1). Em 05/11/2026, a API ficou indisponível por mais de meia hora seguida, e o deploy da versão 0.1.0 falhou.

## Opções descartadas antes dos experimentos

- **Commitar os Parquets no repositório:** já rejeitada pelo ADR-002. Infla o histórico do Git a cada coleta e mistura código com dados.
- **Artefatos do GitHub Actions:** expiram (no máximo 90 dias) e são difíceis de buscar a partir de outra execução do workflow.
- **Cache do GitHub Actions:** é apagado depois de alguns dias sem uso. Inadequado para um dado que precisa sobreviver justamente a uma queda longa da API.

## Experimento A: anexos de release do GitHub

- Foi criada uma release técnica, `dados-brutos`, marcada como pre-release para não aparecer como versão do projeto.
- Um workflow de teste, numa branch de spike, enviou o Parquet de teste para a release (`gh release upload --clobber`) e o baixou de volta numa pasta vazia (`gh release download`).
- **Tempo total do workflow:** 13 segundos.
- **Download público:** o link do arquivo baixou numa janela anônima, sem login.
- **Permissões:** o workflow precisou de `permissions: contents: write`. O token é o `github.token`, criado pelo próprio Actions a cada execução e que expira sozinho. **Nenhum segredo precisou ser cadastrado.**
- **Histórico:** o `--clobber` substitui o arquivo, e a versão anterior se perde. Guardar várias coletas exige nomear cada arquivo com a data.

## Experimento B: dataset no Hugging Face

- Foi preciso criar uma conta e um token do tipo Write.
- O envio foi feito localmente, com a biblioteca `huggingface_hub` carregada só para o experimento (`uv run --with`), sem entrar nas dependências do projeto.
- O nome de usuário da conta (`Nadinne`) é diferente do nome usado no GitHub (`nadinne94`). O `whoami()` da biblioteca descobre o usuário a partir do token.
- O dataset `Nadinne/monitor-parlamentar-dados` foi criado, e o envio gerou um commit: **cada envio vira uma versão, com histórico**, sem nenhum esforço extra.
- **Incidente durante o experimento:** o token apareceu em texto puro num comando do terminal e numa conversa, e precisou ser revogado. Lição: segredos nunca devem aparecer em linha de comando, log ou conversa. No terminal, usar `Read-Host`; no Actions, usar GitHub Secrets.

## Comparação

| Critério | Release do GitHub | Hugging Face |
|---|---|---|
| Conta e segredos necessários | Nenhum: o token do Actions é automático e temporário | Conta nova e um token de escrita, guardado em GitHub Secrets |
| Histórico de versões | Não nativo: exige nomear arquivos por data | Nativo: cada envio é um commit |
| Acesso pelo Actions | `gh`, já instalado nas máquinas do Actions | Biblioteca `huggingface_hub` e o segredo |
| Acesso público para leitura | Sim, por link direto, sem login | Sim, com página própria do dataset |
| Dependência nova no projeto | Nenhuma | `huggingface_hub` |
| Visibilidade para portfólio | Os dados ficam junto do código, no mesmo repositório | Página própria de dataset, mais visível para quem procura dados |

## Recomendação

**Release do GitHub.** O problema a resolver é operacional: o deploy precisa encontrar a última coleta bem-sucedida, de forma confiável, mesmo com a API fora do ar. Para isso, a release atende sem conta nova, sem segredo e sem dependência nova, e o experimento mostrou que o caminho completo pelo Actions funciona em segundos. O incidente com o token reforça a vantagem de não ter segredo nenhum para gerenciar.

A falta de histórico nativo se resolve com uma convenção de nomes: cada coleta grava um arquivo datado (por exemplo, `deputados-2026-11-05.parquet`) e atualiza uma cópia "mais recente". Esse histórico vai ser necessário quando as despesas da cota parlamentar entrarem, porque elas são corrigidas depois de lançadas.

O Hugging Face continua uma boa opção para outro objetivo, que fica para depois: **publicar os dados tratados** (os marts) como um dataset aberto e documentado, com valor de portfólio. Esse uso não exige que ele seja também o armazenamento operacional do pipeline.
