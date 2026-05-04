# Guia da TUI

O NetBox SDK inclui várias aplicações Textual. O ponto de entrada principal é
`nbx tui`, um navegador em tela cheia para recursos NetBox que compartilha a mesma
config, cliente de API e índice de esquema que a CLI e o SDK Python.

Outros pontos de entrada da TUI especializam-se em desenvolvimento, logs, composição guiada de comandos,
exploração GraphQL e inspeção de modelos Django:

- `nbx tui` para o navegador principal
- `nbx dev tui` para a bancada do desenvolvedor
- `nbx graphql tui` para navegação interativa do esquema GraphQL e execução de consultas
- `nbx cli tui` para montagem guiada de comandos
- `nbx tui logs` para o visualizador de logs em tela cheia
- `nbx logs` para o tail de log simples na CLI
- `nbx dev django-model tui` para inspeção de modelos voltada a contribuidores

A TUI principal também descobre recursos de plugins e objetos customizados
dinamicamente. Se um plugin NetBox expõe uma API REST sob `/api/plugins/`, ou
um ObjectType público anuncia um endpoint REST, `nbx tui` e `nbx dev tui` podem
adicionar esses recursos à barra lateral automaticamente e carregar seus dados
como qualquer recurso NetBox integrado.

---

## Lançar a TUI

```bash
nbx tui                    # perfil default
nbx tui --theme dracula    # tema específico
nbx tui --theme            # listar temas disponíveis

nbx demo tui               # perfil demo (demo.netbox.dev)
nbx demo tui --theme dracula

nbx dev tui                # bancada de requisições do desenvolvedor
nbx demo dev tui           # bancada no demo.netbox.dev
nbx graphql tui            # explorador e executor GraphQL
nbx demo graphql tui       # explorador GraphQL no demo.netbox.dev
nbx cli tui                # construtor de comandos guiado
nbx tui logs               # visualizador de logs em tela cheia
nbx logs                   # tail de log simples na CLI
```

---

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Tema ▾   [barra de pesquisa]                     NetBox SDK │
├────────────────┬────────────────────────────────────────────┤
│  Navegação     │  Resultados │ Detalhes │ Filtros          │
│                │                                            │
│  ▼ circuits    │  [Tabela de resultados]                    │
│  ▼ core        │                                            │
│  ▼ dcim        │                                            │
│    ▸ devices   │  [Painel de detalhe quando linha selecionada]│
│    ▸ sites     │                                            │
│    ▸ …         │                                            │
│  ▼ ipam        │                                            │
│    ▸ prefixes  │                                            │
│    ▸ …         │                                            │
│                │                                            │
├────────────────┴────────────────────────────────────────────┤
│  Barra de status / dicas de ajuda                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Abas

### Resultados

A visão principal de dados. Selecionar um recurso na árvore de navegação carrega seus objetos na tabela de resultados. As linhas são renderizadas com colunas priorizadas (`id`, `name`, `status`, `site`, `role`, …).

- `Space` alterna seleção em uma linha.
- `A` alterna todas as linhas visíveis.
- `D` ou clique em uma linha abre a visão de detalhe.

### Detalhes

Mostra os atributos completos do objeto em um painel chave-valor. Para `dcim/interfaces` com cabo conectado, um diagrama ASCII de trace de cabo é renderizado abaixo dos atributos.

### Filtros

Formulário para aplicar filtros de query da API ao recurso atual. Pressione `F` para abrir o modal de filtros.

---

## Árvore de navegação

O painel esquerdo mostra todos os grupos de app NetBox como seções expansíveis. Clique em um recurso para carregar sua lista, ou use navegação por teclado:

- `G` — foca a árvore de navegação
- Setas — move entre nós
- `Enter` — seleciona / expande um nó

### Recursos de plugin

Recursos REST de plugins / objetos customizados são anexados sob um menu `Plugins` automaticamente quando a instância NetBox conectada os expõe sob `/api/plugins/` ou os informa por `/api/core/object-types/`.

- não é necessária lista hardcoded de plugins
- recursos de plugin aparecem em `nbx tui` e `nbx dev tui`
- se o plugin expõe endpoints REST de lista/detalhe, a TUI pode navegar e renderizar os dados retornados como recursos integrados
- modelos privados ou dados de plugins sem endpoints REST são ignorados

---

## Pesquisa

Pressione `/` para focar a barra de pesquisa superior. Digitar filtra a tabela de resultados carregada em tempo real.

---

## Persistência de estado

A TUI salva e restaura:

- Último recurso selecionado
- Filtros aplicados
- Tema ativo

O estado fica sob a raiz de config do NetBox SDK, tipicamente
`~/.config/netbox-sdk/tui_state.json`. Arquivos de estado antigos do `netbox-cli` ainda são
lidos automaticamente quando presentes.

---

## Ver também

- [Bancada do desenvolvedor](dev-workbench.md)
- [TUI GraphQL](graphql.md)
- [Construtor de CLI](cli-builder.md)
- [Visualizador de logs](logs.md)
- [Navegador de modelos Django](django-models.md)
- [Saída de comandos de lançamento](../reference/tui/launch-examples/index.md)
- [Temas](themes.md)
- [Atalhos de teclado](keybindings.md)
