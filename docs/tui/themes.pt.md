# Temas

A TUI inclui quatro temas integrados e suporta temas personalizados ilimitados definidos como arquivos JSON.

---

## Temas integrados

| Nome do tema | Rótulo | Aliases |
|-----------|-------|---------|
| `default` | Default | - |
| `dracula` | Dracula | `dracula-dark` |
| `netbox-dark` | NetBox Dark | `netbox` |
| `netbox-light` | NetBox Light | `light` |

---

## Selecionar um tema

=== "No lançamento"

    ```bash
    nbx tui --theme dracula
    nbx demo tui --theme netbox
    nbx tui --theme netbox-light
    ```

=== "Em tempo de execução"

    Use o menu suspenso **Theme** no canto superior esquerdo da TUI para trocar de tema ao vivo.

=== "Listar temas disponíveis"

    ```bash
    nbx tui --theme
    ```

---

## Conformidade com o tema

A troca de tema não se limita a contêineres de nível superior. Todo widget Textual e subcomponente deve seguir o tema selecionado, incluindo:

- sobreposições e menus suspensos
- barras de abas e indicadores ativos
- cursor da árvore e estados de destaque
- hover e linhas selecionas em listas de opções
- estilização do gutter, linha do cursor, seleção, cursor e placeholder do `TextArea`

Auditorias de tema devem ser recursivas. Para cada widget tematizado, verifique os internos de framework que o Textual monta dentro dele, não apenas o seletor pai. Isso inclui:

- internos de abas como `ContentTab` e `Underline`
- internos de select como `SelectCurrent Static#label`, glifos de seta e `SelectOverlay`
- internos de input como `.input--cursor`, `.input--selection`, `.input--placeholder` e `.input--suggestion`
- internos de estilo de lista como `.option-list--option-*` e classes de estado `ListItem`
- internos de árvore como `.tree--label`, `.tree--guides*`, `.tree--cursor` e estados hover/destaque
- internos de tabela como `.datatable--header`, `.datatable--cursor` e estados hover
- internos de editor como `.text-area--gutter`, `.text-area--cursor-line`, `.text-area--selection` e `.text-area--placeholder`
- internos de rodapé como `.footer-key--key` e `.footer-key--description`
- internos de notificação como `ToastRack`, `ToastHolder`, `Toast` e `.toast--title`

Quando um widget personalizado compõe widgets Textual aninhados internamente, propague a intenção semântica do tema até esses filhos e verifique os estados finais renderizados dos filhos após uma troca de tema em tempo de execução, incluindo foco, hover, ativo, sobreposição e caminhos ANSI.

Regras do projeto:

- Nunca hardcode cores em tempo de execução em Python ou TCSS fora de `netbox_tui/themes/*.json`
- Nunca deixe cores padrão do Textual visíveis após troca de tema
- Evite paletas de widgets integradas quando contornam os tokens de tema do repositório; estilize classes de componente com variáveis semânticas

### Depurar incompatibilidades específicas de tema

Se um tema integrado renderiza corretamente e outro ainda mostra blocos de cor estranhos, não assuma sempre que o problema é seletor de widget. Compare a própria paleta JSON do tema com um tema integrado conhecido como bom antes de adicionar mais sobrescritas TCSS.

Use este fluxo:

- compare `background`, `surface`, `panel`, `boost`, `nb-border` e `nb-border-subtle` entre o tema problemático e um tema integrado bom
- verifique se a hierarquia de superfícies escuras é progressiva: `background < surface < panel < boost` em luminosidade percebida
- para temas escuros, mantenha a pilha de superfícies com saturação baixa o suficiente para que camadas de painel leiam como estrutura neutra, não blocos azul-violeta brilhantes
- verifique caminhos ANSI do Textual separadamente, porque `Screen` / `ModalScreen` e widgets aninhados do framework ainda podem aplicar padrões ANSI em terminal real mesmo quando testes headless parecem corretos

Lição prática do ajuste Dracula:

- os fundos azuis restantes do modal de suporte e dos painéis Dev-TUI não eram apenas vazamentos de estilo de widget
- os próprios tokens `surface` / `panel` / `boost` / borda do Dracula estavam muito azuis comparados à pilha mais calma do NetBox Dark
- a correção durável foi em duas partes:
  - rebalancear a hierarquia de superfícies Dracula em `netbox_tui/themes/dracula.json`
  - contabilizar explicitamente o comport ANSI de tela/modal do Textual e widgets internos montados em tempo de execução

Ao revisar ou criar um tema escuro, trate o seguinte como verificação de sanidade integrada:

- superfícies devem ficar progressivamente mais claras do fundo do app ao ênfase de painel aninhado
- tokens de superfície adjacentes não devem saltar demais em saturação
- tokens de borda devem separar regiões sem parecer contornos neon
- corpos modais e painéis de conteúdo grandes devem parecer estrutura neutra, não blocos coloridos de recurso

---

## Criar um tema personalizado

Coloque um arquivo JSON em `netbox_tui/themes/`. Será descoberto automaticamente — sem alterações de código.

### Estrutura obrigatória

```json
{
  "name": "my-theme",
  "label": "My Theme",
  "dark": true,
  "aliases": ["my", "mytheme"],
  "colors": {
    "primary":    "#BD93F9",
    "secondary":  "#6272A4",
    "warning":    "#FFB86C",
    "error":      "#FF5555",
    "success":    "#50FA7B",
    "accent":     "#FF79C6",
    "background": "#282A36",
    "surface":    "#343746",
    "panel":      "#21222C",
    "boost":      "#414558"
  },
  "variables": {
    "nb-success-text":    "#82D18E",
    "nb-success-bg":      "#1C3326",
    "nb-info-text":       "#79C0FF",
    "nb-info-bg":         "#172131",
    "nb-warning-text":    "#F2CC60",
    "nb-warning-bg":      "#332B00",
    "nb-danger-text":     "#FF7B7B",
    "nb-danger-bg":       "#3B1111",
    "nb-border":          "#414558",
    "nb-border-subtle":   "#343746",
    "nb-muted-text":      "#6272A4",
    "nb-link-text":       "#8BE9FD",
    "nb-id-text":         "#FFB86C",
    "nb-key-text":        "#F1FA8C",
    "nb-tag-text":        "#FF79C6",
    "nb-tag-bg":          "#3A1F3A"
  }
}
```

### Campos obrigatórios

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Identificador único usado em flags da CLI |
| `label` | string | Nome legível |
| `dark` | boolean | Se é tema escuro |
| `colors` | object | 10 chaves semânticas de cor Textual (todas obrigatórias) |

### Campos opcionais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `aliases` | array de strings | Nomes alternativos para este tema |
| `variables` | object | 16 sobrescritas de variáveis CSS específicas do NetBox |

### Regras de validação

Temas são validados estritamente no carregamento:

- Todas as 10 chaves `colors` são obrigatórias
- Todas as 16 chaves `variables` são obrigatórias quando o objeto `variables` está presente
- Todos os valores de cor devem ser strings hex `#RRGGBB`
- Não são permitidos nomes de tema duplicados ou conflitos de alias
- Chaves de nível superior desconhecidas causam erro

Um tema malformado levanta `ThemeCatalogError` com mensagem clara indicando qual chave ou valor falhou.

---

## Diretrizes de design

Temas devem seguir a hierarquia visual do modo escuro do NetBox:

- Use `primary` para elementos interativos e anéis de foco
- Use `surface` para fundos de cartão/painel
- Use `panel` para contêineres aninhados
- Use `boost` para fundos destacados
- Use `nb-border` para bordas padrão, `nb-border-subtle` para bordas internas/secundárias
- Cores de status: `nb-success-*`, `nb-info-*`, `nb-warning-*`, `nb-danger-*`

Orientação adicional de superfície para temas escuros:

- `background` deve ser a fundação neutra mais escura
- `surface` deve elevar levemente de `background` sem ficar obviamente colorido
- `panel` deve ficar acima de `surface` para contêineres aninhados e corpos modais
- `boost` deve ser a camada de ênfase neutra mais forte, não substituto de cor de destaque
- se a pilha de superfícies de um tema lê como lajes azuis ou roxas em painéis grandes, reduza a saturação nesses tokens estruturais antes de corrigir widgets

Veja `reference/design/NETBOX-DARK-PATTERNS.md` no repositório para a referência de design completa.
