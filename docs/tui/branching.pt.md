# Branching

Quando o plugin
[`netbox-branching`](https://github.com/netboxlabs/netbox-branching) está
instalado no NetBox de destino, a TUI principal ganha dois pontos de
interação adicionais:

## Ctrl+B — Trocador de branch

Um atalho global abre um modal listando todas as branches. Use as setas e
**Enter** para ativar; **Escape** sai sem alterar nada. A primeira entrada,
**"main (no active branch)"**, limpa a branch ativa.

```
┌── Switch Branch ─────────────────────────────────────────┐
│ Enter to activate · Escape to cancel                     │
│                                                          │
│   main (no active branch)                                │
│ ● td5smq0f · feature-x   [ready]                         │
│   ab12cd34 · hotfix      [merged]                        │
└──────────────────────────────────────────────────────────┘
```

## Pílula no topbar

Quando há uma branch ativa, uma pílula colorida
**`● <schema_id> · <name>`** aparece no topbar (à esquerda do breadcrumb).
Em `main` (sem branch ativa) nenhuma pílula é mostrada — o topbar
permanece inalterado. A pílula é totalmente removida quando o plugin não
está instalado.

## Persistência

A branch ativa é persistida no arquivo `tui_state.*.json` específico para
cada base-URL, dentro do diretório de configuração. Na próxima vez que a
TUI for aberta contra o mesmo host NetBox, a branch é reaplicada
automaticamente.

Se a detecção de funcionalidade indicar mais tarde que o plugin foi
removido, o estado persistido é limpo na inicialização.

## Como o header se propaga

Ao ativar uma branch, o header `X-NetBox-Branch` é gravado no dicionário
`persistent_headers` do cliente SDK. Toda requisição — inclusive as
disparadas por tasks `@work` em background no Textual — usa esse header,
mantendo recarregamentos de listas, paineis de detalhe e navegadores
dinâmicos de recursos consistentes com a branch ativa.
