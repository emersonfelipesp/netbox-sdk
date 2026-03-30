# Padrão de composição Textual

O `netbox-sdk` usa um padrão de composição estilo React para trabalho de UI Textual: construir telas a partir de widgets pequenos reutilizáveis, passar configuração por argumentos de construtor e compor comportamento aninhando widgets em vez de árvores profundas de herança.

## Por quê

- mantém o layout legível em `compose()`
- torna regras de tema e estilo reutilizáveis
- permite que widgets pequenos evoluam independentemente
- reduz acoplamento frágil à classe base
- mapeia bem ao modelo de composição de UI do lado Python do próprio NetBox

## Regra principal

Prefira composição a herança para estrutura de UI.

Use herança quando:

- estender um primitivo Textual com comportamento estreito e reutilizável como `NbxButton`
- criar um widget stateful autocontido com API pública clara

Prefira composição quando:

- montar cabeçalhos, corpos, barras de ferramentas e regiões de conteúdo
- compartilhar estrutura visual entre várias telas
- expressar “slots” como áreas cabeçalho/corpo/rodapé

## Mapeamento React

Padrão React:

```tsx
<Panel>
  <PanelHeader title="Object Attributes" subtitle="NetBox detail-style panel" />
  <PanelBody>
    <Status />
    <Table />
    <Trace />
  </PanelBody>
</Panel>
```

Padrão Textual neste repositório:

```python
class ObjectAttributesPanel(Vertical):
    def compose(self):
        yield NbxPanelHeader("Object Attributes", "NetBox detail-style panel")
        with NbxPanelBody(id="detail_panel_body"):
            yield Static("Ready", id="detail_status")
            yield DataTable(id="detail_table")
            yield Static("Cable Trace", id="detail_trace_title", classes="hidden")
            yield Static("", id="detail_trace", classes="hidden")
```

## Blocos de construção padrão

Primitivos de composição compartilhados atuais ficam em `netbox_tui/widgets.py`:

| Primitivo | Papel |
|-----------|------|
| `NbxButton` | Botão tematizado com props semânticas `tone`, `size`, `chrome` |
| `NbxPanelHeader` | Barra de título do painel |
| `NbxPanelBody` | Contêiner de conteúdo do painel com `tone` / `surface` opcionais |
| `ContextBreadcrumb` | Breadcrumb clicável na barra superior com menus suspensos escopados; emite `CrumbSelected` / `MenuOptionSelected` |
| `SupportModal` | `ModalScreen` autocontida compartilhada pelas TUIs principal e dev; herda tema ativo via classe CSS no mount |

Estes devem ser o ponto de partida padrão para novas peças de UI reutilizáveis.

## Diretrizes

### 1. Compor telas a partir de widgets folha

Mantenha `App.compose()` focado em arranjar regiões principais.

- shell do app
- barra superior
- barra lateral
- workspace principal
- sobreposições

Mova subárvores repetidas para widgets dedicados quando tiverem significado.

### 2. Trate argumentos de construtor como props React

Entradas de widget devem ser explícitas e semânticas.

Bom:

```python
NbxButton("Send", size="medium", tone="primary")
NbxButton("Close", size="small", tone="error")
NbxPanelHeader("Object Attributes", "NetBox detail-style panel", tone="primary")
NbxPanelBody(surface="background")
```

Evite passar intenção de estilo indiretamente por strings de classe ad hoc quando um argumento semântico seria mais claro.

### 2.1 Valores de tema também devem ser props

Widgets reutilizáveis conscientes de tema devem receber entradas de estilo semânticas por argumentos de construtor, similar a props React.

Preferido:

```python
NbxButton("Send", size="medium", tone="primary")
NbxPanelHeader("Danger Zone", tone="error")
NbxPanelBody(surface="panel")
```

Evite:

```python
Button("Send", classes="custom-primary custom-medium")
Static("Danger Zone", classes="red-header")
```

Use props semânticas como:

- `size`
- `tone`
- `surface`
- `chrome`

Composição consciente de tema também inclui propagação de superfície. Se um widget reutilizável monta primitivos Textual aninhados internamente, o widget pai deve levar a intenção de tema semântica até esses filhos e verificar as superfícies finais renderizadas.

Exemplos importantes:

- widgets modais devem tematizar o contêiner do diálogo e botões de ação, não só o `ModalScreen`
- widgets com abas devem tematizar `TabbedContent`, `ContentTabs`, `ContentSwitcher` e o `TabPane` ativo
- widgets de editor/lista devem tematizar tanto o contêiner externo quanto as partes internas de framework que pintam fundos em foco ou caminhos ANSI

### 3. Use widgets aninhados como slots

Quando um widget tem regiões reconhecíveis, modele-as como widgets filhos em vez de um monólito grande.

- cabeçalho
- corpo
- rodapé
- barra de ferramentas
- estado vazio

### 4. Mantenha métodos públicos focados em comportamento

Um widget composto deve expor métodos de nível de intenção como:

- `set_loading()`
- `set_object()`
- `set_trace()`

Evite vazar estrutura interna de filhos a menos que o chamador realmente possua essa estrutura.

### 5. Mantenha estilo no TCSS

Composição define estrutura. TCSS define aparência.

- use classes semânticas em widgets reutilizáveis
- mantenha lógica de tema em TCSS e JSON de tema
- evite decisões de cor em tempo de execução em construtores de widget

Exceção:

- quando padrões de runtime do Textual ainda sobrescrevem o tema selecionado em caminhos só de terminal como `Screen` / `ModalScreen` ANSI-mode ou subwidgets internos montados, adicione uma sincronização estreita de superfície em runtime no widget ou app dono
- se usar essa saída, documente o motivo nos docs de tema/design relevantes e mantenha a sobrescrita limitada a tokens de tema semânticos

Regra prática:

- primeiro corrija a paleta do tema se os tokens estruturais estão errados
- depois corrija seletores TCSS recursivos para internos de framework
- só então adicione sincronização de superfície em runtime para widgets específicos que ainda escapam do contrato de tema

### 6. Mantenha herança rasa

Não crie cadeias longas de herança de widget para reutilização de layout.

Preferido:

- `ObjectAttributesPanel(Vertical)` composto de `NbxPanelHeader` e `NbxPanelBody`

Evite:

- `BasePanel -> PanelCard -> DetailPanel -> ObjectAttributesPanel -> SpecializedPanel`

## Padrão em todo o projeto

Para novo trabalho Textual em `netbox-sdk`:

1. Comece com composição.
2. Passe intenção de tema/estilo como props semânticas em widgets reutilizáveis.
3. Extraia primitivos visuais reutilizáveis para `netbox_tui/widgets.py`.
4. Documente novos primitivos na documentação de contribuidor se se tornarem padrão do projeto.
5. Só adicione herança quando o widget for realmente um primitivo especializado em comportamento.
