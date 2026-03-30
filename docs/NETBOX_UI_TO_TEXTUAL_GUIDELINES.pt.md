# Diretrizes de design NetBox UI para TUI Textual

Este documento resume como o frontend do NetBox é construído e define uma estratégia prática de port para uma TUI baseada em Textual no `netbox-sdk`.

## 1. Arquitetura do frontend NetBox (o que existe hoje)

## 1.1 Stack e build

A UI web do NetBox é construída a partir de:

- templates Django (HTML renderizado no servidor)
- SCSS → CSS empacotado
- TypeScript → JavaScript empacotado
- HTMX para atualizações parciais de página
- Primitivas de UI Bootstrap/Tabler/TomSelect

Referências principais:

- `netbox/docs/development/web-ui.md`
- `netbox/netbox/project-static/src/*.ts`
- `netbox/netbox/project-static/styles/*.scss`
- `netbox/netbox/templates/**/*.html`

## 1.2 Esqueleto de página em runtime

A composição central da página vem de:

- `templates/base/base.html`: assets globais, bootstrap de tema, boot JS, contêiner de mensagens
- `templates/base/layout.html`: barra lateral, barra de pesquisa superior, área de conteúdo, rodapé, modais

A UI do NetBox usa consistentemente estas zonas:

- Barra lateral de navegação esquerda (menus agrupados)
- Zona superior de pesquisa/entrada
- Área de conteúdo principal (abas + cartões + tabelas/formulários)
- Linha de rodapé/status
- Contêiner de sobreposição modal

## 1.3 UI como componentes declarativos (lado Python)

Uma escolha de design chave do NetBox é que o conteúdo da página não é só templates brutos; é composto a partir de classes de UI Python:

- `netbox/ui/layout.py`: `Layout -> Row -> Column`
- `netbox/ui/panels.py`: abstrações reutilizáveis de `Panel`
- `netbox/ui/attrs.py`: atributos tipados de objeto (texto, escolha, bool, objeto aninhado, imagem, etc.)
- declarações de painel em nível de app, por exemplo `dcim/ui/panels.py`

Esta composição declarativa é importante para paridade TUI porque mapeia naturalmente para composição de widgets Textual.

Para o `netbox-sdk`, isto é agora uma diretriz do projeto: usar uma abordagem de composição estilo React no Textual construindo telas a partir de widgets pequenos reutilizáveis e primitivos de layout aninhados em vez de árvores profundas de herança.

## 1.4 Modelo de interação lista/detalhe

Páginas comuns:

- Visão de lista: `templates/generic/object_list.html`
- Visão de detalhe: `templates/generic/object.html`

Páginas de lista incluem:

- busca rápida
- aba de filtros
- tabela ordenável/paginada
- seleção em massa/ações
- configuração de tabela

Páginas de detalhe incluem:

- breadcrumbs + identidade do objeto
- botões de ação (editar/excluir/favorito/etc.)
- seções com abas
- grade de painéis (linhas/colunas/cartões)

## 1.5 Atualizações dinâmicas/parciais

O NetBox usa HTMX fortemente para atualizações de tabela e conteúdo modal:

- `templates/htmx/table.html`
- `templates/inc/table_htmx.html`
- `templates/inc/table_controls_htmx.html`
- `templates/inc/htmx_modal.html`
- `project-static/src/htmx.ts`

Padrão: interação do usuário atualiza só o fragmento necessário; listeners do lado cliente são reinicializados após o swap.

## 1.6 Estado e comportamento do frontend

Módulos de comportamento notáveis:

- `src/netbox.ts`: pipeline central de inicialização
- `src/sidenav.ts`: estado da barra lateral + fixar/desafixar + comportamento responsivo
- `src/hotkeys.ts`: atalhos globais (ex.: `/` foca busca)
- `src/search.ts`: UX de busca rápida
- `src/tableConfig.ts`: persistência de preferências de tabela via API
- `src/colorMode.ts` + `js/setmode.js`: persistência de modo claro/escuro
- `src/state/index.ts`: gerenciador de estado com localStorage

## 1.7 Sistema visual

Estrutura SCSS:

- `styles/_variables.scss`: fontes, espaçamento, cores, largura da barra lateral
- `styles/netbox.scss`: imports (base + overrides + transitional + custom)
- `styles/transitional/*`: camada de compatibilidade para primitivas de UI comuns

A semântica visual é baseada em tokens (variáveis primeiro), não estilo inline ad hoc.

## 2. Princípios de port para Textual

## 2.1 Preservar primeiro a arquitetura da informação

Não comece pelos widgets. Comece pela semântica de página do NetBox:

- Hierarquia de navegação (menu/grupo/item)
- Fluxos de lista (buscar/filtrar/ordenar/paginar/massa)
- Fluxos de detalhe (painéis + abas + ações)
- Padrões de feedback (alertas/toasts/status)

No Textual, isso vira:

- Shell do app com navegação esquerda persistente + busca/comando superior + corpo de conteúdo + rodapé
- Modos de tela para lista/detalhe/editar/ações
- Widgets de painel compartilhados para renderização consistente de objetos

## 2.2 Mapear primitivos NetBox para primitivos Textual

Mapeamento sugerido:

- Menu lateral → `Tree` ou `ListView` com seções agrupadas
- Abas → `TabbedContent` + `TabPane`
- Cartões/Painéis → contêineres `Widget` personalizados com linha título/ação
- Tabelas de atributos → `DataTable` de duas colunas ou widget lista chave/valor
- Tabelas de lista de objetos → `DataTable` com estado de ordenação/filtro
- Diálogos modais → `ModalScreen`
- Toast/mensagens → widget de notificação + canal de status no rodapé
- Swap parcial HTMX → métodos de atualização/refresh direcionados ao widget

## 2.2.1 Usar composição estilo React no Textual

Trate widgets Textual como o React trata componentes:

- argumentos de construtor são props
- `compose()` é a árvore de render
- estrutura reutilizável deve ser extraída em widgets pequenos
- telas complexas devem montar widgets filhos em vez de herdar de classes base grandes

Exemplos padrão do projeto:

- `NbxButton(label, size=\"small\" | \"medium\" | \"large\")`
- `NbxButton(label, tone=\"primary\" | \"error\" | ...)`
- `NbxPanelHeader(title, subtitle, tone=...)`
- `NbxPanelBody(surface=...)`

Padrão preferido:

- `ObjectAttributesPanel(Vertical)` composto de primitivos cabeçalho/corpo
- decisões de tema reutilizáveis passadas como props semânticas em vez de classes ad hoc

Evite:

- cadeias de herança criadas só para reutilizar markup ou layout

## 2.3 Recriar comportamento de refresh incremental

Atualizações parciais do HTMX devem virar refresh assíncrono em nível de widget:

- Nunca recarregue a tela inteira para pequenas mudanças de tabela/filtro
- Mantenha workers separados para:
  - dados da tabela
  - metadados de filtro
  - contagens da barra lateral (opcional)
- Re-renderize só regiões alteradas (set-diff de linhas/células `DataTable`)

## 2.4 Manter backend CLI/TUI compartilhado

A web NetBox e a API separam apresentação de dados. Faça o mesmo:

- uma camada de serviço API (já em `netbox_cli/api.py` + `services.py`)
- CLI e TUI chamam os mesmos métodos de serviço
- sem lógica de negócio específica da TUI para semântica CRUD

## 2.5 Tratar tema como tokens

Espelhe a estratégia de tokens do NetBox em variáveis CSS Textual:

- definir tokens de cor base (surface, panel, accent, danger, muted)
- definir tokens de layout (largura da barra lateral, espaçamento de painel)
- suportar alternância claro/escuro persistida na config local (similar à persistência do modo de cor do NetBox)

Regra de implementação de tema para este projeto:

- estilizar o widget externo não basta; sempre inspecione e tematize internos aninhados do Textual recursivamente
- verifique seletores filhos de framework e classes de componente como internos de aba, sobreposições de select, partes de cursor/seleção/placeholder de input, estados de option-list, estados de cursor/destaque de árvore, estados de datatable, internos de text-area, internos de rodapé e internos de toast
- se um widget personalizado envolve outros widgets Textual, passe props de tema semânticas a esses filhos e verifique o resultado renderizado após troca de tema em runtime
- aceitação de tema deve incluir estados de foco, hover, ativo, selecionado, sobreposição e ANSI, não só aparência em repouso

Regra de depuração de tema para este projeto:

- se um tema integrado parece correto e outro ainda renderiza blocos de cor estranhos, compare os tokens de superfície JSON do tema antes de adicionar mais sobrescritas de widget
- compare especificamente `background`, `surface`, `panel`, `boost`, `nb-border` e `nb-border-subtle` com um tema integrado conhecido como bom
- para temas escuros, tokens estruturais devem permanecer neutros o suficiente para que painéis grandes e corpos modais leiam como contêineres em camadas em vez de lajes coloridas brilhantes
- se a pilha de tokens está errada, corrija primeiro a paleta do tema e só então seletores recursivos de widget

Regra de runtime Textual:

- testes headless não bastam para sign-off de tema
- o Textual tem padrões ANSI separados para superfícies como `Screen` e `ModalScreen`, e estes ainda podem vencer em terminais reais
- se TCSS sozinho não amarra totalmente esses caminhos de runtime ao tema selecionado, adicione uma sincronização estreita de superfície em runtime usando tokens de tema semânticos para o modal, pilha de painéis ou subárvore de widget interna afetada

## 3. Blueprint concreto de port para netbox-sdk

## 3.1 Layout do shell

Crie um shell de app raiz que espelhe `base/layout.html`:

- painel nav esquerdo: hierarquia app/recurso
- barra superior: busca rápida global + contexto ativo
- painel principal: conteúdo dinâmico (lista/detalhe/editar)
- rodapé: status, conexão, hora do servidor, perfil ativo

## 3.2 Modelo de navegação

O backend do menu NetBox é filtrado por permissão e agrupado (`navigation/menu.py`, `templatetags/navigation.py`).

Equivalente TUI:

- construir árvore de menu a partir de grupos/recursos OpenAPI agora
- depois enriquecer com permissões dirigidas pela API e perfil de usuário
- ações rápidas por item equivalentes a botões de menu (adicionar/importar)

## 3.3 Contrato de tela de lista

Para cada tela de lista de recurso:

- Entrada de busca rápida (tecla `/` para focar, igual UX web)
- Painel de filtros (painel lateral alternável ou aba)
- `DataTable` ordenável/paginada
- Modelo de seleção em massa (selecionar visíveis/selecionar todos correspondentes)
- Barra de ações (adicionar/exportar/edição em massa/excluir)

Mantenha estado de lista em um objeto de store local explícito análogo ao estado frontend do NetBox:

- query
- filtros aplicados
- ordenação
- página/per_page
- IDs selecionados
- colunas visíveis

## 3.4 Contrato de tela de detalhe

Para cada detalhe de objeto:

- linha de breadcrumb/contexto
- título + identificador do objeto
- botões de ação primários
- faixa de abas para visões auxiliares
- grade de painéis a partir de specs declarativas de painel

Implemente classes de painel na TUI análogas às classes `Panel` do NetBox:

- `ObjectAttributesPanelWidget`
- `RelatedObjectsPanelWidget`
- `JsonPanelWidget`
- `ObjectsTablePanelWidget`

## 3.5 Camada de renderização de atributos

O NetBox tem atributos tipados em `ui/attrs.py`. Recrie esta ideia:

- um pequeno registro de renderizadores de atributo TUI:
  - texto
  - numérico + unidade
  - badge de escolha/status
  - booleano
  - caminho de objeto aninhado
  - JSON
- comportamento central de placeholder para valores nulos

Isso evita deriva de formatação por tela.

## 3.6 Padrões modais e quick-add

O NetBox usa `htmx_modal` + fluxos quick-add. Equivalente Textual:

- use `ModalScreen` para diálogos criar/editar
- em sucesso ao salvar:
  - atualize o widget fonte (ex.: opções de select, linhas de tabela)
  - feche o modal
  - mostre notificação

## 3.7 Semântica de mensagem e erro

Toasts NetBox e mensagens do servidor devem mapear para:

- notificações não bloqueantes para sucesso/info
- painel de erro persistente para falhas
- status transitório no rodapé para operações em segundo plano

Para erros de API, exiba:

- status HTTP
- payload `detail`/validação analisado
- dica/ação de retry

## 3.8 Atalhos e acessibilidade

Porte primeiro comportamento crítico de teclado:

- `/` foca busca
- `g` foca grupos/nav
- `s` foca tabela de recursos
- `r` atualiza visão atual
- `q` sair/voltar conforme contexto
- tratamento de escape em modal

Evite atalhos que conflitem com foco de entrada de texto.

## 4. O que não portar 1:1

Não clone detalhes específicos da web sem valor para TUI:

- semântica de classes Bootstrap
- breakpoints responsivos baseados em pixel
- comportamento de popovers/tooltips específico de navegador
- eventos de swap DOM

Porte a *intenção do fluxo de trabalho*, não a mecânica HTML.

## 5. Marcos mínimos de paridade viável

1. Paridade de navegação
- Árvore grupo/recurso OpenAPI + paleta de comandos/busca com salto

2. Paridade de lista
- query/filtrar/ordenar/página/seleção em massa para recursos principais (`dcim.devices`, `ipam.prefixes`, `ipam.ip-addresses`)

3. Paridade de detalhe
- cabeçalho de objeto + atributos em painéis + tabela de objetos relacionados

4. Paridade de ação
- criar/editar/excluir e ações em massa comuns

5. Paridade de UX
- tokens de tema, notificações, atalhos, preferências persistentes

## 6. Notas de implementação para netbox-sdk

Recomendações imediatas:

- Introduzir pacote `netbox_tui/` com abstrações de painel e tela (espelhando a camada `ui/` do NetBox)
- Adicionar módulo de estado local para persistência de estado de visão lista/detalhe
- Padronizar utilitários de transformação resposta → tabela/attr para manter formatação CLI/TUI consistente
- Manter um caminho de contrato API e evitar lógica ramificada entre CLI e TUI

Esta abordagem preserva a estrutura de UX comprovada do NetBox ao adotar padrões de interação nativos do Textual.
