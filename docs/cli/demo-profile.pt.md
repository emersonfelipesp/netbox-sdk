# Perfil demo

O perfil `demo` permite executar a maior parte dos fluxos `nbx` contra a instância pública
[demo.netbox.dev](https://demo.netbox.dev) com a mesma forma de CLI e TUI do seu runtime normal.

---

## Configuração com Playwright

O `nbx demo init` usa Playwright para abrir um navegador Chromium headless, entrar em `demo.netbox.dev`, criar um token de API novo e armazená-lo automaticamente:

```bash
nbx demo init
# solicita usuário e senha de demo.netbox.dev
```

Para CI ou uso scriptado, passe credenciais como flags:

```bash
nbx demo init --username nbxuser --password mypassword --headless
```

Quando você inicializa o perfil demo assim, o `nbx` também armazena o usuário e a senha demo no mesmo arquivo de config privado para poder atualizar automaticamente o token demo depois se `demo.netbox.dev` reiniciar e começar a retornar `Invalid v1 token`.

**Opções de `nbx demo init`**

| Flag | Descrição |
|------|-----------|
| `--username` / `-u` | usuário demo.netbox.dev (solicitado se omitido) |
| `--password` / `-p` | senha demo.netbox.dev (solicitada se omitida) |
| `--headless` / `--headed` | Playwright headless (padrão) ou com janela visível |
| `--token-key` | Pular Playwright — definir token diretamente |
| `--token-secret` | Pular Playwright — definir token diretamente |

!!! tip "Instalação do Playwright"
    Instale o Playwright e o navegador Chromium antes de executar `nbx demo init`:

    ```bash
    uv tool run --from playwright playwright install chromium --with-deps
    ```

---

## Configuração direta de token

Se você já tem um token de API demo, pule o Playwright:

```bash
# token v2 (chave + segredo)
nbx demo init --token-key <key> --token-secret <secret>

# token v1 (string única) — defina token_version manualmente em config.json
nbx demo --token-key "" --token-secret <40-char-token>
```

---

## Verificar a config demo

```bash
nbx demo config
nbx demo config --show-token   # revela valores do token
```

A saída da config também mostra se há credenciais de login demo disponíveis para atualização automática do token.

---

## Executar comandos contra o demo

A árvore de subcomandos `nbx demo` espelha a árvore completa do `nbx`, usando o token do perfil demo e `https://demo.netbox.dev` como URL base:

```bash
nbx demo dcim devices list
nbx demo ipam prefixes list -q status=active
nbx demo dcim sites list --json
nbx demo dcim interfaces get --id 4 --trace
nbx demo call GET /api/status/
nbx demo dev tui
```

Se o token demo salvo expirou porque a instância demo pública reiniciou de noite, o `nbx` tentará automaticamente provisionar um token demo novo usando o usuário e a senha demo salvos antes de expor a falha de autenticação.

---

## TUI demo

```bash
nbx demo tui
nbx demo tui --theme dracula
```

Lança a TUI Textual já conectada à instância demo.

---

## Dev TUI demo

```bash
nbx demo dev tui
nbx demo dev tui --theme dracula
```

Lança a bancada de requisições do desenvolvedor conectada ao demo, para inspecionar caminhos e executar requisições contra `demo.netbox.dev` sem trocar de perfil.

---

## Construtor de CLI demo

```bash
nbx demo cli tui
```

Lança a TUI de construtor de comandos guiado no perfil demo.

---

## Dev HTTP demo

`nbx demo dev http` espelha `nbx dev http`: os mesmos verbos (`get`, `post`, `put`, `patch`, `delete`, `paths`, `ops`) e flags de saída (`--json`, `--yaml`, `--markdown`) se aplicam, e cada chamada HTTP usa o perfil demo.

```bash
nbx demo dev http get --path /api/status/
nbx demo dev http get --path /dcim/devices/ -q limit=3 --markdown
```

---

## Reset

Remover credenciais demo salvas:

```bash
nbx demo reset
```

---

## Como o perfil demo é armazenado

O perfil demo fica junto ao perfil default em
`~/.config/netbox-sdk/config.json`:

```json
{
  "profiles": {
    "default": { "...": "..." },
    "demo": {
      "base_url": "https://demo.netbox.dev",
      "token_version": "v1",
      "token_key": null,
      "token_secret": "40-character-token-here",
      "demo_username": "nbxuser",
      "demo_password": "mypassword",
      "timeout": 30.0
    }
  }
}
```

Arquivos de config antigos do `netbox-cli` ainda são lidos automaticamente por compatibilidade.
A `base_url` do perfil demo é sempre fixada em
`https://demo.netbox.dev` independentemente do que está armazenado no arquivo de config.
O arquivo de config é gravado com permissões privadas só do usuário para que as credenciais demo
permaneçam locais à sua máquina.
