# Autenticação

O NetBox suporta dois formatos de token. O SDK trata ambos de forma transparente.

---

## Versões de token

=== "v2 (padrão)"

    O NetBox 4.x emite tokens v2 em duas partes: um prefixo **chave** e um sufixo **segredo**, combinados como `nbt_<key>.<secret>`.

    ```python
    from netbox_sdk import Config

    cfg = Config(
        base_url="https://netbox.example.com",
        token_version="v2",
        token_key="abc123",         # a parte após "nbt_"
        token_secret="def456xyz",   # o sufixo secreto
    )
    ```

    O cabeçalho `Authorization` enviado ao NetBox será:
    ```
    Bearer nbt_abc123.def456xyz
    ```

=== "v1 (legado)"

    Instâncias NetBox mais antigas usam um único token opaco:

    ```python
    cfg = Config(
        base_url="https://netbox.example.com",
        token_version="v1",
        token_secret="abcdef1234567890abcdef1234567890abcdef12",
    )
    ```

    O cabeçalho `Authorization` será:
    ```
    Token abcdef1234567890abcdef1234567890abcdef12
    ```

---

## Fallback automático v2 → v1

Se sua configuração especifica v2 mas a instância NetBox rejeita o token Bearer com `"Invalid v2 token"`, o cliente tenta novamente automaticamente com o cabeçalho v1 `Token <secret>`. Isso cobre instâncias que têm tokens v1 armazenados mas são acessadas com config v2.

---

## Auxiliares de cabeçalho de auth

```python
from netbox_sdk.config import authorization_header_value, resolved_token

cfg = Config(base_url="...", token_version="v2", token_key="k", token_secret="s")

resolved_token(cfg)              # "nbt_k.s"
authorization_header_value(cfg)  # "Bearer nbt_k.s"
```

---

## Armazenamento de perfis

O SDK armazena perfis de conexão nomeados em `~/.config/netbox-sdk/config.json`
(ou `$XDG_CONFIG_HOME/netbox-sdk/config.json`).

Se você já tem um arquivo de config histórico do `netbox-cli`, o SDK ainda o lê
automaticamente até que uma nova config NetBox SDK seja gravada.

```python
from netbox_sdk.config import (
    load_profile_config,
    save_profile_config,
    clear_profile_config,
    DEFAULT_PROFILE,
)

# Carrega o perfil "default" (aplica substituições de variáveis de ambiente automaticamente)
cfg = load_profile_config()
cfg = load_profile_config(DEFAULT_PROFILE)   # o mesmo

# Salva um perfil personalizado
save_profile_config("production", cfg)
save_profile_config("staging", staging_cfg)

# Carrega um perfil nomeado (sem substituições por variáveis de ambiente)
staging = load_profile_config("staging")

# Remove um perfil
clear_profile_config("staging")
```

### Segurança do arquivo

O diretório de config é criado com modo `0o700` e o arquivo de config com `0o600` para impedir que outros usuários no mesmo sistema leiam suas credenciais.

---

## Substituições por variáveis de ambiente

Somente para o **perfil default**, estas variáveis de ambiente substituem valores do disco:

| Variável | Campo na config |
|----------|-----------------|
| `NETBOX_URL` | `base_url` |
| `NETBOX_TOKEN_KEY` | `token_key` |
| `NETBOX_TOKEN_SECRET` | `token_secret` |

Variáveis de ambiente têm precedência sobre valores armazenados. Útil para CI/CD:

```bash
NETBOX_URL=https://netbox.example.com \
NETBOX_TOKEN_KEY=mykey \
NETBOX_TOKEN_SECRET=mysecret \
python your_script.py
```

```python
from netbox_sdk.config import load_config

cfg = load_config()   # aplica as variáveis de ambiente
```

---

## Validar configuração

```python
from netbox_sdk.config import is_runtime_config_complete

if not is_runtime_config_complete(cfg):
    print("Faltam base_url ou credenciais de token")
```

Isso verifica se `base_url`, `token_secret` e (para v2) `token_key` estão presentes.

---

## Normalização de URL

O campo `base_url` é normalizado na atribuição:

- Adiciona `https://` se nenhum esquema for informado
- Remove barras finais
- Rejeita credenciais embutidas (`user:pass@host`)
- Rejeita esquemas não HTTP (`ftp://`, `file://`)
- Rejeita query strings e fragmentos

```python
from netbox_sdk.config import normalize_base_url

normalize_base_url("netbox.example.com")         # "https://netbox.example.com"
normalize_base_url("http://netbox.example.com/") # "http://netbox.example.com"
normalize_base_url("ftp://netbox.example.com")   # levanta ValueError
```
