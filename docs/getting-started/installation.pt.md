# Instalação

O `netbox-sdk` requer Python 3.11 ou mais recente.

## Via PyPI

Somente SDK:

```bash
pip install netbox-sdk
```

O pacote base já inclui as dependências necessárias para o SDK assíncrono e o
SDK tipado versionado, incluindo `pydantic` e `email-validator`.

CLI:

```bash
pip install 'netbox-sdk[cli]'
```

TUI:

```bash
pip install 'netbox-sdk[tui]'
```

Tudo:

```bash
pip install 'netbox-sdk[all]'
```

## Com a ferramenta uv

```bash
uv tool install --force 'netbox-sdk[cli]'
nbx --help
```

## A partir do código-fonte

```bash
git clone https://github.com/emersonfelipesp/netbox-sdk.git
cd netbox-sdk
uv sync --dev --extra cli --extra tui --extra demo
uv run nbx --help
```

## Suporte ao SDK tipado

O repositório inclui bundles OpenAPI versionados e modelos Pydantic gerados para
NetBox `4.5`, `4.4` e `4.3`. Não é necessário executar geração de código localmente.

## Qual instalação escolher?

- `pip install netbox-sdk` se você só precisa do SDK Python
- `pip install 'netbox-sdk[cli]'` se você quer o comando `nbx`
- `pip install 'netbox-sdk[tui]'` se você quer lançar TUIs Textual a partir do
  pacote em um ambiente Python existente
- `pip install 'netbox-sdk[all]'` se você quer todas as interfaces disponíveis localmente

## Fluxo do contribuidor

```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
uv run pytest
```

## Automação demo opcional

O `nbx demo init` usa Playwright. O runtime do navegador deve ser instalado separadamente:

```bash
uv tool run --from playwright playwright install chromium --with-deps
```
