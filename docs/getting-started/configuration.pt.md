# Configuração

O `netbox-sdk` armazena configurações de conexão em um arquivo JSON e suporta dois
perfis nomeados: `default` e `demo`.

---

## Configuração interativa

Execute `nbx init` para ser solicitado sobre os detalhes da conexão NetBox:

```bash
nbx init
```

Será solicitado:

- **URL base do NetBox** — por exemplo `https://netbox.example.com`
- **Chave do token** — a parte chave de um token de API v2
- **Segredo do token** — a parte secreta de um token de API v2
- **Timeout** — timeout HTTP em segundos (padrão: 30)
- **Verificação TLS** — opcional; veja [HTTPS e verificação TLS](#https-and-tls-verification)

Qualquer comando que exija conexão também solicita automaticamente se a config estiver ausente.

---

## HTTPS e verificação TLS {#https-and-tls-verification}

Para URLs **HTTPS** base, o SDK verifica o certificado TLS do servidor usando o armazém de confiança do sistema (mesmo padrão do `ssl` do Python).

### Quando a verificação falha (autoassinado ou CA privada)

Se o servidor usar certificado autoassinado ou uma CA que não está no armazém do sistema, a primeira conexão falha com erro de verificação de certificado.

**Preferência não definida (`ssl_verify` omitido ou `null`):** a CLI e as TUIs podem solicitar uma vez para:

- **Desativar a verificação** para este perfil — salvo como `"ssl_verify": false` (inseguro; use apenas em redes confiáveis).
- **Manter a verificação ativa** — salvo como `"ssl_verify": true`; você deve corrigir a cadeia de certificados ou adicionar a CA emissora ao armazém de confiança do sistema.

Depois da escolha, a preferência é salva e você não é solicitado novamente para aquele perfil, salvo se editar a config.

**Preferência explícita:** se `ssl_verify` já for `true` ou `false` na config, as ferramentas não solicitam; respeitam o valor.

### `nbx init`

```bash
# Persistir verificação explicitamente ligada ou desligada (recomendado para automação)
nbx init --base-url https://netbox.example.com --token-key KEY --token-secret SECRET --verify-ssl
nbx init ... --no-verify-ssl
```

Omita ambas as flags para deixar `ssl_verify` indefinido até a primeira conexão (por padrão verifica em tempo de execução, com solicitação opcional em caso de falha).

### Variável de ambiente

Somente para o **perfil default**, `NETBOX_SSL_VERIFY` substitui o valor armazenado quando definida:

| Valor | Efeito |
|-------|--------|
| `1`, `true`, `yes`, `on` | Verificar certificados |
| `0`, `false`, `no`, `off` | Desativar verificação |

Remova a variável para usar o valor de `config.json`.

### `nbx test`

O `nbx test` testa a API usando o perfil ativo. Se a verificação falhar e `ssl_verify` estiver indefinido, a mesma escolha interativa acima é oferecida antes do comando encerrar.

### TUIs Textual

Quando uma verificação de saúde da conexão falha por motivo de certificado e `ssl_verify` estiver indefinido, a TUI principal, o construtor de CLI, a bancada do desenvolvedor e o inspetor de modelos Django podem exibir um modal: **Manter verificação** ou **Desativar verificação** (salvo no perfil).

### Campo no arquivo de config

Adicione `ssl_verify` opcional a um perfil (booleano ou omitir / `null`):

```json
"default": {
  "base_url": "https://netbox.example.com",
  "token_version": "v2",
  "token_key": "abc123",
  "token_secret": "xyz789",
  "timeout": 30.0,
  "ssl_verify": false
}
```

---

## Localização do arquivo de config

| Condição | Caminho |
|----------|---------|
| `XDG_CONFIG_HOME` definido | `$XDG_CONFIG_HOME/netbox-sdk/config.json` |
| Padrão | `~/.config/netbox-sdk/config.json` |

Arquivos de config antigos do `netbox-cli` ainda são lidos automaticamente se o novo
caminho `netbox-sdk` ainda não existir.

O arquivo usa uma estrutura `profiles`:

```json
{
  "profiles": {
    "default": {
      "base_url": "https://netbox.example.com",
      "token_version": "v2",
      "token_key": "abc123",
      "token_secret": "xyz789",
      "timeout": 30.0,
      "ssl_verify": null
    },
    "demo": {
      "base_url": "https://demo.netbox.dev",
      "token_version": "v1",
      "token_key": null,
      "token_secret": "40-char-token-string",
      "timeout": 30.0
    }
  }
}
```

---

## Substituições por variáveis de ambiente

As variáveis a seguir substituem apenas o **perfil default**:

| Variável | Campo na config |
|----------|-----------------|
| `NETBOX_URL` | `base_url` |
| `NETBOX_TOKEN_KEY` | `token_key` |
| `NETBOX_TOKEN_SECRET` | `token_secret` |
| `NETBOX_SSL_VERIFY` | `ssl_verify` (veja [HTTPS e verificação TLS](#https-and-tls-verification)) |

Variáveis de ambiente têm precedência sobre valores armazenados, mas não são gravadas em disco.

---

## Formatos de token

O NetBox suporta dois formatos de token:

=== "Tokens v2 (padrão)"

    Tokens v2 têm chave e segredo separados, combinados em um cabeçalho `Bearer`:

    ```
    Authorization: Bearer nbt_<KEY>.<SECRET>
    ```

    Na configuração: `token_key` = parte chave, `token_secret` = parte secreta.

=== "Tokens v1 (legado)"

    Tokens v1 são uma única string opaca, enviada como:

    ```
    Authorization: Token <TOKEN>
    ```

    Na configuração: deixe `token_key` vazio, defina `token_secret` com o token completo.
    Defina `token_version` como `"v1"` no arquivo de config.

O `netbox-sdk` tenta novamente automaticamente uma requisição v2 falha com formato v1 ao receber 401 ou 403, então versões de token mal configuradas costumam ser corrigidas de forma transparente.

---

## Ver a config atual

```bash
nbx config              # mostra base_url, timeout, status do token
nbx config --show-token # também mostra chave e segredo do token em texto plano
```

Exemplo de saída:

```json
{
  "base_url": "https://netbox.example.com",
  "timeout": 30.0,
  "token_version": "v2",
  "ssl_verify": null,
  "token": "set",
  "token_key": "set",
  "token_secret": "set"
}
```

`ssl_verify` é `true`, `false` ou `null` quando nenhum valor explícito foi armazenado ainda.

---

## Vários perfis

O perfil `demo` é separado do `default` e sempre aponta para `https://demo.netbox.dev`. É gerenciado pela árvore de subcomandos `nbx demo`. Veja [Perfil demo](../cli/demo-profile.md) para detalhes.
