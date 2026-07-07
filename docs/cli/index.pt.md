# CLI

`nbx` é a interface de linha de comando do NetBox SDK. Compartilha configuração,
descoberta de esquema e lógica de requisição com o SDK Python e a camada TUI.

Há seis modos complementares de interação:

| Modo | Exemplo | Quando usar |
|------|---------|-------------|
| **Dinâmico** | `nbx dcim devices list` | Operações do dia a dia — auto-descoberto via OpenAPI |
| **HTTP explícito** | `nbx call GET /api/status/` | Caminhos personalizados, exploração em massa da API |
| **Descoberta** | `nbx groups` / `nbx resources dcim` | Aprender o que está disponível |
| **GraphQL** | `nbx graphql "{ sites { name } }"` | Consultas entre recursos e experimentação de esquema |
| **Jobs de plugin** | `nbx proxbox sync -t storage` | Fluxos guiados para APIs de job de plugins |
| **CRUD Proxbox** | `nbx proxbox firewall rules patch --id 7` | Catálogo, CRUD e TUI dedicados ao `netbox-proxbox` |

---

## Visão geral da árvore de comandos

```
nbx
├── init                    configura o perfil default
├── config                  mostra a configuração atual
├── groups                  lista todos os grupos de app OpenAPI
├── resources GROUP         lista recursos de um grupo
├── ops GROUP RESOURCE      lista operações de um recurso
├── graphql                 executa consultas GraphQL
├── call METHOD PATH        requisição HTTP explícita
├── proxbox                 catálogo, CRUD, sync e TUI Proxbox
│   ├── resources           lista recursos do catálogo Proxbox
│   ├── ops RESOURCE        lista operações de um recurso Proxbox
│   ├── tui                 lança a bancada de requisições Proxbox
│   ├── sync                agenda job de sync e transmite progresso
│   ├── sync-types          lista tipos de sync Proxbox disponíveis
│   └── <família> <recurso> comandos gerados list/get/create/update/patch/delete
├── tui                     lança o navegador Textual principal
├── logs                    mostra logs estruturados recentes da aplicação
├── cli                     auxiliares específicos da CLI
│   └── tui                 lança o construtor de comandos guiado
├── docs                    ferramentas de geração de documentação
│   └── generate-capture    captura saída da CLI em docs/generated/
├── demo                    perfil demo.netbox.dev
│   ├── init                autentica em demo.netbox.dev
│   ├── config              mostra config do perfil demo
│   ├── reset               remove credenciais demo salvas
│   ├── tui                 lança TUI com perfil demo
│   ├── cli                 construtor de comandos no perfil demo
│   │   └── tui             construtor guiado no perfil demo
│   ├── dev                 ferramentas de desenvolvedor no perfil demo
│   │   ├── tui             lança Dev TUI no perfil demo
│   │   └── django-model    inspeciona modelos Django do NetBox
│   └── <group> <resource>  mesma árvore da raiz, usando perfil demo
├── dev                     ferramentas de desenvolvedor e interfaces experimentais
│   ├── tui                 lança bancada de requisições do desenvolvedor
│   ├── http                auxiliares HTTP diretos para caminhos arbitrários da API
│   └── django-model        montar/buscar/navegar modelos Django do NetBox
└── <group>                 grupo de app OpenAPI (dcim, ipam, …)
    └── <resource>          recurso (devices, prefixes, …)
        ├── list            endpoint GET de lista
        ├── get             endpoint GET de detalhe (requer --id)
        ├── create          POST
        ├── update          PUT (requer --id)
        ├── patch           PATCH (requer --id)
        └── delete          DELETE (requer --id)
```

---

- [Comandos](commands.md) para o conjunto de comandos de nível superior
- [Comandos dinâmicos](dynamic-commands.md) para operações de recursos orientadas por OpenAPI
- [Proxbox](proxbox.md) para catálogo, CRUD, sync e TUI dedicados ao `netbox-proxbox`
- [GraphQL](graphql.md) para uso específico de GraphQL
- [Perfil demo](demo-profile.md) para a árvore `nbx demo`
- [Saída de comandos capturados](../reference/cli/command-examples/index.md) para exemplos gerados da CLI
