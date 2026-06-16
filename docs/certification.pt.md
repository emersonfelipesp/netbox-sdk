# Prontidão para certificação

`netbox-sdk` está preparado para revisão como pacote de integração ou SDK do
ecossistema NetBox. Ele não é um plugin do NetBox.

## Por que esta não é uma aplicação de plugin

`netbox-sdk` roda fora do NetBox e se conecta ao NetBox por superfícies públicas
de API. Ele não instala uma aplicação Django no NetBox, não usa `PLUGINS` e não
fornece modelos, templates, views ou navegação dentro do NetBox. Campos
específicos de plugin, como nome de configuração, ícone de plugin e capturas da
interface de plugin no NetBox, portanto, não se aplicam.

A evidência de certificação se concentra em qualidade de pacote,
compatibilidade de API, testes, documentação, suporte e manutenibilidade.

## Checklist de evidências

| Área | Evidência |
| --- | --- |
| Licença | Apache-2.0 em `LICENSE.txt` e nos metadados do pacote |
| Metadados do pacote | `pyproject.toml` declara URLs do projeto, faixa de Python, licença SPDX, arquivos de licença, entry points, extras opcionais e dados de pacote |
| Suporte Python | Python 3.11, 3.12 e 3.13 |
| Compatibilidade NetBox | Linhas de SDK tipado para NetBox `4.6`, `4.5`, `4.4` e `4.3` |
| Validação live NetBox | A CI executa testes live do SDK contra NetBox `v4.6.3`, `v4.6.2` e `v4.5.10` |
| Validação offline | API mock do NetBox, testes do cliente tipado, testes de schema, suítes SDK/CLI/TUI e testes de segurança |
| Validação de pacote | Build, `twine check` e smoke test de instalação/importação do wheel na CI |
| Documentação | README e site MkDocs cobrindo instalação, autenticação, requisições, SDK tipado, schema, erros, branching, API mock, CLI e TUI |
| Suporte | GitHub issues para bugs, funcionalidades e pedidos de documentação |

## Matriz de compatibilidade

| Release `netbox-sdk` | Python | Linhas de API NetBox tipadas | Alvos live NetBox na CI |
| --- | --- | --- | --- |
| `0.0.9.post2` | `>=3.11,<3.14` | `4.6`, `4.5`, `4.4`, `4.3` | `v4.6.3`, `v4.6.2`, `v4.5.10` |

Versões patch normalizam para sua linha de release no SDK tipado. Por exemplo,
`4.6.2` usa o cliente tipado `4.6` versionado no repositório.

## Dependências

Dependências base do SDK declaradas em `pyproject.toml`:

- `aiohttp`
- `pydantic`
- `email-validator`
- `rich`
- `pyyaml`

Extras opcionais:

- `cli`: interface de linha de comando com Typer
- `tui`: aplicações de terminal com Textual
- `mock`: API mock do NetBox com FastAPI/uvicorn
- `demo`: automação do ambiente demo com Playwright
- `branching`: extra marcador para fluxos com NetBox Branching
- `all`: todas as superfícies opcionais para usuário

## Pacote para aplicação de certificação

Use o seguinte enquadramento:

- **Tipo de pacote:** Pacote de integração / SDK
- **Repositório:** <https://github.com/emersonfelipesp/netbox-sdk>
- **Pacote PyPI:** `netbox-sdk`
- **Documentação:** <https://emersonfelipesp.github.io/netbox-sdk/>
- **Canal principal de suporte:** GitHub issues
- **Nome de configuração de plugin:** Não aplicável
- **Configuração `PLUGINS` no NetBox:** Não aplicável
- **Capturas da UI de plugin do NetBox:** Não aplicável; capturas das
  superfícies de terminal estão na documentação da TUI

O arquivo raiz `CERTIFICATION.md` contém o pacote de evidências do repositório e
o checklist de release.
