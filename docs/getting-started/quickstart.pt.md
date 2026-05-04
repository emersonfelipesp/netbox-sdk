# Início rápido

Coloque em funcionamento a interface que você realmente pretende usar.

--8<-- "snippets/documented-release-pt.md"

---

## 1. Instalar e configurar o runtime compartilhado

```bash
pip install 'netbox-sdk[all]'
nbx init
# informe sua URL do NetBox e token de API quando solicitado
```

Fixado à versão documentada:

```bash
--8<-- "snippets/pip-pinned-all.txt"
nbx init
# informe sua URL do NetBox e token de API quando solicitado
```

---

## 1a. Setup do contribuidor

Se você desenvolve o próprio `netbox-sdk`, use o ambiente local do repositório e instale os hooks Git:

```bash
cd /path/to/netbox-sdk
uv sync --dev --extra cli --extra tui --extra demo
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
```

---

## 2. Usar a CLI

```bash
# listar todos os grupos de app OpenAPI
nbx groups

# listar recursos em um grupo
nbx resources dcim

# listar operações para um recurso específico
nbx ops dcim devices
```

---

## 3. Consultar dados

```bash
# listar todos os dispositivos
nbx dcim devices list

# obter um dispositivo específico por ID
nbx dcim devices get --id 1

# filtrar resultados
nbx dcim devices list -q name=switch01
nbx dcim devices list -q site=nyc01 -q status=active

# saída em JSON, YAML ou Markdown
nbx dcim devices list --json
nbx ipam prefixes list --yaml
nbx dcim devices list --markdown
```

---

## 4. Lançar a TUI principal

```bash
nbx tui
nbx dev tui
nbx cli tui
nbx logs
```

Use o navegador principal para navegação do dia a dia, a bancada dev para inspeção
de requisições, o construtor de CLI para montar comandos de forma interativa e `nbx logs`
para inspecionar o log compartilhado da aplicação.

---

## 5. Criar, atualizar, excluir

```bash
# criar um novo endereço IP
nbx ipam ip-addresses create --body-json '{"address":"192.0.2.10/24","status":"active"}'

# criar a partir de um arquivo
nbx dcim devices create --body-file ./new-device.json

# atualizar um dispositivo
nbx dcim devices update --id 42 --body-json '{"status":"planned"}'

# patch de um único campo
nbx dcim devices patch --id 42 --body-json '{"comments":"rack shelf 3"}'

# excluir
nbx dcim devices delete --id 42
```

---

## 6. Experimentar o perfil demo

```bash
nbx demo init          # autentica em demo.netbox.dev via Playwright
nbx demo dcim devices list
nbx demo tui
```

Não é necessária uma instância NetBox pessoal. O `demo.netbox.dev` é um ambiente
público e expõe as mesmas superfícies de CLI e TUI sob `nbx demo ...`.

---

## 7. Usar o SDK diretamente

```python
import asyncio

from netbox_sdk import api


async def main() -> None:
    nb = api("https://netbox.example.com", token="your-token")
    device = await nb.dcim.devices.get(42)
    if device is not None:
        print(device.name)


asyncio.run(main())
```

---

## 8. Usar o SDK tipado

```python
import asyncio

from netbox_sdk import typed_api


async def main() -> None:
    nb = typed_api(
        "https://netbox.example.com",
        token="your-token",
        netbox_version="4.5",
    )
    device = await nb.dcim.devices.get(42)
    if device is not None:
        print(device.name)


asyncio.run(main())
```

O cliente tipado valida requisições e respostas com modelos Pydantic versionados
para NetBox `4.6`, `4.5`, `4.4` e `4.3`.

---

## Próximos passos

- [Guia do SDK](../sdk/index.md) para entrypoints Python e transporte
- [Guia da CLI](../cli/index.md) para `nbx`, GraphQL e capturas de comandos
- [Guia da TUI](../tui/index.md) para o navegador principal e TUIs especializadas
