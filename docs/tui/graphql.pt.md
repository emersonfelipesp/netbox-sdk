# TUI GraphQL

O `nbx graphql tui` lança uma interface Textual dedicada para explorar o
esquema GraphQL do NetBox e executar consultas GraphQL reais a partir do terminal.

Complementa o comando único `nbx graphql QUERY`. O caminho CLI é melhor
para execução direta e scripts; a TUI é melhor quando você precisa inspecionar
a estrutura do esquema, navegar argumentos e refinar consultas iterativamente.

## Lançamento

```bash
nbx graphql tui
nbx graphql tui --theme dracula
nbx graphql tui --theme

nbx demo graphql tui
nbx demo graphql tui --theme dracula
```

O ponto de entrada demo usa o mesmo fluxo de autenticação do perfil demo que o resto
do SDK. A execução de consultas passa pelo caminho compartilhado `NetBoxApiClient.graphql()`,
mantendo alinhamento entre atualização de token demo e comportamento do perfil de produção.

## Layout

A TUI GraphQL é dividida em três áreas de trabalho:

- um explorador de campos raiz com pesquisa e histórico de consultas salvas
- um construtor de consulta com editores de consulta e variáveis
- um painel de resposta com abas de corpo, cabeçalhos e resumo da execução

A barra superior também expõe seleção de tema, status da conexão, contexto do campo,
suporte e controles de fechamento.

## Exploração de esquema

Na inicialização o app executa uma consulta de introspecção GraphQL contra a instância
conectada e constrói um modelo de explorador a partir do esquema retornado.

O explorador apresenta:

- campos de consulta raiz
- argumentos de campo, tipos, padrões e descrições
- tipos de retorno para campos selecionados
- dicas de seleção de objetos aninhados
- campos de objetos de entrada usados por argumentos de filtro e paginação
- tipos possíveis de union e interface para scaffolding de fragmentos inline

Use `/` para focar a caixa de pesquisa de campo e filtrar a lista de campos raiz em tempo
real.

## Construção guiada de consultas

A TUI GraphQL nunca prende você só ao fluxo do construtor. O editor de consulta é
texto GraphQL editável, mas a barra de ação pode inserir esqueletos úteis:

- `Build Field` gera uma consulta mínima para o campo raiz selecionado
- `Insert Args` insere todos os argumentos do campo com placeholders conscientes do tipo
- `Insert Filters` insere um objeto `filters:` quando disponível
- `Insert Pagination` insere um objeto `pagination:` quando disponível
- `Insert Fragments` insere fragmentos inline para retornos union ou interface

Esses trechos são intencionalmente mínimos para você refiná-los manualmente.

## Variáveis e execução

A aba Variables aceita um objeto JSON. Deixe em branco quando a consulta não
usa variáveis.

Executar uma consulta mostra:

- status HTTP e estado de erro GraphQL
- duração da requisição
- tamanho da resposta
- corpo JSON formatado
- cabeçalhos da resposta
- um resumo curto da execução incluindo chaves de dados e erros GraphQL

Erros GraphQL são exibidos mesmo quando o status HTTP é `200`.

## Histórico e persistência

A TUI salva estado por instância sob a raiz de config do NetBox SDK. Esse estado
inclui:

- tema selecionado
- último texto de consulta
- último texto de variáveis
- campo raiz selecionado
- histórico recente de consultas

O histórico é escopado pela URL base do NetBox, então instâncias demo e produção mantêm
seus próprios conjuntos de consultas.

## Fallback de introspecção

Algumas implantações NetBox podem desativar introspecção ou retornar erros de esquema. Quando
isso ocorre a TUI GraphQL ainda abre em modo editor primeiro. Você pode continuar
enviando consultas GraphQL manuais, e a barra lateral indica que a navegação do esquema está
indisponível no momento.

## Relação com outras interfaces

- `nbx graphql QUERY` é o executor CLI direto para requisições GraphQL
- `nbx graphql tui` é o explorador GraphQL interativo
- `nbx dev tui` é a bancada do desenvolvedor focada em REST
- `nbx tui` é o navegador geral de recursos com superfície REST/OpenAPI

## Capturas de tela e saída gerada de lançamento

- [Galeria de capturas da TUI GraphQL](screenshots-graphql.md)
- [Referência de saída de lançamento da TUI](../reference/tui/launch-examples/index.md)
