# Guia do desenvolvedor

Documentação técnica para contribuidores e quem constrói em cima do `netbox-sdk`.

- [Arquitetura](architecture.md) — mapa de módulos, direção de dependências entre os três pacotes, fluxo de dados e empacotamento
- [Internos do SDK](sdk-internals.md) — como os módulos de cliente, config, esquema, fachada, cache e serviços funcionam internamente
- [Integração com proxbox-api](integration-with-proxbox-api.md) — factory de sessão, helpers REST, concorrência, cache, retentativa e padrões de integração do mundo real
- [Integração de pacotes](package-integration.md) — extras PyPI, `netbox_sdk` / `netbox_cli` / `netbox_tui`, regras de import
- [Princípios de design](design-principles.md) — convenções alinhadas a SOLID para este repositório
- [Padrão de composição Textual](textual-composition.md) — diretriz de composição estilo React para widgets Textual
- [Geração de documentação](docgen.md) — sistema de captura de comandos e fluxo de CI
- [Suporte de IDE](ide-support.md) — workspace do VS Code, Pylance via marcadores PEP 561 e gates duplos `ty` + `pyright`

## Gates de qualidade para pull requests

Pull requests do Gitea direcionados a `main` executam
`.gitea/workflows/ci.yml` sem segredos no runner isolado
`ci-untrusted-python312`. O gate verifica o ambiente travado, a política dos
workflows, ty, Pyright, pre-commit em todos os arquivos, a suíte mock offline
completa, todos os módulos de segurança do SDK/CLI/TUI, MkDocs estrito,
metadados da distribuição e um smoke test do wheel instalado. Ele não pode
publicar, implantar, enviar commits ou acessar um serviço NetBox real.

O GitHub continua responsável pelas matrizes Python 3.11–3.13 e NetBox real. O
Gitea valida `refs/pull/<N>/head`; a proteção da branch deve exigir que o head do
PR esteja atualizado com `main`, além de exigir todos os contextos terminais.
Um job na fila com `runner_id: 0` é evidência ausente e nunca deve ser tratado
como aprovação.
