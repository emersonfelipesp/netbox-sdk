# Guia do desenvolvedor

Documentação técnica para contribuidores e quem constrói em cima do `netbox-sdk`.

- [Arquitetura](architecture.md) — mapa de módulos, direção de dependências entre os três pacotes, fluxo de dados e empacotamento
- [Internos do SDK](sdk-internals.md) — como os módulos de cliente, config, esquema, fachada, cache e serviços funcionam internamente
- [Integração com proxbox-api](integration-with-proxbox-api.md) — factory de sessão, helpers REST, concorrência, cache, retentativa e padrões de integração do mundo real
- [Integração de pacotes](package-integration.md) — extras PyPI, `netbox_sdk` / `netbox_cli` / `netbox_tui`, regras de import
- [Princípios de design](design-principles.md) — convenções alinhadas a SOLID para este repositório
- [Padrão de composição Textual](textual-composition.md) — diretriz de composição estilo React para widgets Textual
- [Geração de documentação](docgen.md) — sistema de captura de comandos e fluxo de CI
