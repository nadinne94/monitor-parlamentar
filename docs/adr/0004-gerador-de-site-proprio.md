# ADR-004: Gerador de site estático próprio (substitui o Evidence)

- **Status:** Proposto
- **Data:** 2026-10-30
- **Decisora:** Nadinne
- **Substitui:** a decisão sobre o site no [ADR-002](0002-stack-tecnologica.md)

## Contexto

O ADR-002 escolheu o Evidence.dev para gerar o site estático. Ao montar o esqueleto do repositório (Incremento 0), constatou-se que o projeto Evidence mudou de rumo:

- O template oficial agora cria projetos do **Evidence Studio**, produto que funciona com conexão ao vivo a um banco de dados e publicação pela própria plataforma, mediante login.
- Os comandos `npm run build` e `npm run dev` do template atual apenas exibem aviso de descontinuação.
- O gerador estático open source passou a ser tratado como "Legacy Evidence", com guia oficial de migração para o Studio.

Continuar com o Legacy Evidence significaria basear o site numa ferramenta que o próprio fornecedor está descontinuando. Adotar o Evidence Studio contraria dois requisitos do ADR-002: execução totalmente local e ausência de dependência de plataforma, justamente o problema que encerrou o projeto anterior.

O risco já estava previsto no ADR-002 ("Evidence.dev é uma ferramenta mais jovem... trocar de ferramenta de site não afeta o pipeline"), e o contrato canônico (ADR-003) torna a troca barata: o site só lê os marts.

## Decisão

O site é gerado por um módulo Python próprio (`monitor.site`), usando **Jinja2** para templates HTML:

- Lê exclusivamente tabelas do contrato canônico no DuckDB.
- Renderiza uma página inicial e, a partir do Incremento 1, uma página por deputado a partir de um único template.
- Grava o resultado em `build/site/`, publicado no GitHub Pages pelo workflow de deploy.
- CSS próprio, sem framework e sem fontes externas. Gráficos, quando necessários, entram como SVG gerado no build ou uma biblioteca JavaScript leve carregada localmente, decisão a tomar no incremento que precisar.
- Templates usam `StrictUndefined`: uma variável ausente faz o build falhar, em vez de gerar página com campo vazio.

## Alternativas consideradas

**Legacy Evidence.** Rejeitada pelo risco de descontinuação descrito acima.

**Evidence Studio.** Rejeitada: depende de plataforma e login, contrariando o ADR-002.

**Observable Framework.** Viável tecnicamente, mas adiciona Node.js e JavaScript como segunda stack para um site que, no MVP, é essencialmente texto, tabelas e números. Não foi possível confirmar com segurança o ritmo atual de manutenção do projeto.

**Quarto.** Bom para relatórios, mas menos natural para gerar centenas de páginas parametrizadas (uma por deputado por mês).

## Consequências

**Positivas**

- Uma única linguagem (Python) no projeto inteiro; Node.js deixa de ser pré-requisito.
- Nenhuma dependência de fornecedor no site.
- O site entra na mesma suíte de testes: cada template é testado com pytest, incluindo estados vazios.
- Controle total sobre acessibilidade, desempenho e o que é publicado (ex.: mascaramento de CPF garantido no código e testado).

**Negativas**

- Mais trabalho de frontend manual (HTML e CSS) do que com uma ferramenta de BI como código.
- Componentes prontos (tabelas ordenáveis, filtros, gráficos interativos) precisam ser construídos ou escolhidos à parte.
- Ganho de aprendizado deslocado: menos ferramenta de BI, mais desenvolvimento web básico.
