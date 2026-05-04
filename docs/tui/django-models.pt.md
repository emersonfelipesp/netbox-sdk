# Navegador de modelos Django

O navegador de modelos Django é a TUI mais especializada do repositório. Destina-se
a contribuidores e operadores avançados que precisam inspecionar o grafo interno de
modelos Django do NetBox em vez de interagir com a API REST.

## Comandos

```bash
nbx dev django-model build
nbx dev django-model tui

nbx demo dev django-model tui
```

## Fluxo

1. Construir ou buscar cache do grafo de modelos.
2. Lançar a TUI contra esse cache.
3. Inspecionar modelos, relacionamentos e trechos de fonte de forma interativa.

O cache é gravado sob a raiz de config do NetBox SDK em novas instalações, com
suporte de compatibilidade para caminhos de cache antigos do `netbox-cli`.

## Melhores casos de uso

- inspeção de modelos voltada a contribuidores
- depuração de esquema e relacionamentos
- validar como modelos fonte do NetBox mapeiam para o comportamento da API

## Capturas de tela

- [Galeria do navegador de modelos Django](screenshots-django.md)
