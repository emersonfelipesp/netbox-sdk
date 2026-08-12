# Ponte para Plugins NetBox

A ponte para plugins permite que qualquer plugin NetBox anuncie um conjunto
pequeno de operações semânticas através da sua API REST existente. O
`netbox-sdk` descobre e valida essas operações, e o `netbox_mcp` as expõe por
duas ferramentas MCP estáveis: `plugin_list_tools` e `plugin_call_tool`.

A ponte não cria um segundo servidor dentro do plugin. Autenticação,
autorização, limitação, tratamento da requisição e a própria operação continuam
nas views normais do Django REST Framework do plugin. O SDK permanece como o
único cliente HTTP e reutiliza o perfil NetBox selecionado ou o token por
chamada.

## Anúncio

Um plugin participante adiciona um membro `mcp` à resposta da raiz da sua API.
Para um plugin chamado `example`, o único local aceito na versão 1 é:

```json
{
  "mcp": {
    "schema_version": "1",
    "manifest": "/api/plugins/example/mcp/"
  }
}
```

O link do manifesto deve ter a mesma origem e permanecer dentro do namespace do
plugin anunciante. Instalações NetBox sob um prefixo de URL podem anunciar a
forma prefixada (por exemplo, `/netbox/api/plugins/example/mcp/`); o SDK a
normaliza para a base configurada antes do envio. Um plugin que não anuncia esse
membro é simplesmente ignorado.

## Contrato do manifesto

`GET /api/plugins/example/mcp/` retorna um documento versionado:

```json
{
  "schema_version": "1",
  "plugin": "example",
  "tools": [
    {
      "name": "run_report",
      "title": "Executar relatório de inventário",
      "description": "Monta o relatório visível ao principal NetBox atual.",
      "method": "POST",
      "path": "reports/run/",
      "effect": "write",
      "inputSchema": {
        "type": "object",
        "properties": {
          "scope": {"type": "string", "enum": ["active", "all"]}
        },
        "required": ["scope"],
        "additionalProperties": false
      },
      "outputSchema": {
        "type": "object",
        "properties": {"job_id": {"type": "integer", "minimum": 1}},
        "required": ["job_id"],
        "additionalProperties": false
      },
      "annotations": {
        "readOnlyHint": false,
        "destructiveHint": false,
        "idempotentHint": false,
        "openWorldHint": false
      }
    }
  ]
}
```

A versão 1 é o protocolo genérico de descritor, não uma cópia congelada do
payload de ferramentas de um plugin específico. Cada plugin é responsável por
versionar as operações do seu manifesto enquanto preserva estas regras do
descritor. A versão 1 tem regras intencionalmente restritas:

- `plugin` e nomes de ferramentas usam identificadores estáveis em minúsculas.
  Os nomes são únicos em um manifesto e aparecem como `plugin.tool` no catálogo.
- `path` é um caminho relativo fixo abaixo de `/api/plugins/<plugin>/`.
  Caminhos absolutos, URLs, query strings, fragmentos, codificação percentual,
  barras invertidas, segmentos vazios e segmentos-ponto são rejeitados.
- Operações `GET` e `HEAD` declaram `effect: read`. Métodos de escrita declaram
  `write` ou `destructive`; `DELETE` deve ser destrutivo. As anotações MCP devem
  concordar com o efeito declarado.
- `inputSchema` usa JSON Schema Draft 2020-12 estrito, com `type: object` e
  `additionalProperties: false`. A versão 1 aceita apenas o subconjunto limitado
  de palavras-chave documentado e exclui referências/definições, padrões regex,
  formatos não suportados, schemas condicionais e combinadores. A versão 1 só
  suporta o formato `date-time`, validado como RFC 3339, incluindo a sintaxe de
  segundo intercalar. Um valor `:60` só é aceito quando seu instante normalizado
  em UTC cruza o limite de um mês; segundos intercalares em minutos arbitrários
  e datas cujo ajuste de segundo intercalar ou fuso horário ultrapassaria o
  calendário suportado são rejeitados. Tokens JSON inteiros
  permanecem exatos e obedecem aos limites do schema. Valores JSON de ponto
  flutuante matematicamente inteiros são aceitos somente até o limite
  interoperável `9007199254740991`; valores maiores são rejeitados para impedir
  que arredondamento selecione outro identificador. `uniqueItems` só é
  aceito para arrays com um único domínio escalar de tipo explícito; tipos
  escalares mistos são rejeitados. Essas restrições evitam buscas remotas,
  contratos recursivos, formatos ignorados silenciosamente e amplificação
  desnecessária.
- Propriedades de entrada de `GET`/`HEAD` devem ser escalares ou arrays de
  escalares, os únicos valores codificados de modo determinístico na query.
- Todo corpo retornado pelo destino deve ser JSON estrito e finito e respeita
  limites de tamanho, profundidade e nós mesmo sem `outputSchema`. `HEAD` e
  respostas HTTP 204/205 são as exceções sem corpo e retornam `body: null`.
  Quando presente, o schema também valida respostas bem-sucedidas com corpo
  antes do retorno. Se uma escrita foi enviada, mas sua resposta não indicar
  sucesso, for redirecionada, ilegível ou inválida, o MCP informa que o resultado
  é desconhecido e alerta para não repetir a operação às cegas. Falhas locais de
  argumentos e headers ocorrem antes desse limite de ambiguidade e podem ser
  corrigidas com segurança.
- Manifestos, schemas, quantidade de ferramentas, tamanho de entrada/saída,
  profundidade e quantidade de nós são limitados. Uma varredura aceita no
  máximo 128 raízes de plugins, 512 ferramentas agregadas, 257 requisições, 2
  MiB de corpos agregados e 30 segundos no total. O limite agregado restante é
  aplicado durante o streaming de cada resposta pela quantidade descompactada
  de bytes antes da decodificação, e corpos de respostas sem sucesso também são
  contabilizados. Cada manifesto aceita 256 KiB e 64 ferramentas; cada corpo do
  destino aceita 256 KiB.

O schema anunciado é um contrato com quem chama, não um mecanismo de
autorização. A view DRF de destino deve continuar aplicando as permissões NetBox
normais e validar o mesmo corpo da requisição.

## Uso pelo MCP

Descubra um plugin ou todos os plugins participantes:

```json
{
  "plugin": "example"
}
```

Passe esse objeto para `plugin_list_tools`. O resultado inclui o descritor
validado, o nome qualificado e o caminho resolvido. Durante uma varredura de
todos os plugins, um anúncio inválido aparece em `problems` sem ocultar plugins
válidos. Selecionar diretamente o plugin inválido falha de forma segura.

Invoque uma ferramenta listada com `plugin_call_tool`:

```json
{
  "plugin": "example",
  "tool": "run_report",
  "arguments": {"scope": "active"},
  "dry_run": true
}
```

Leituras são enviadas logo após descoberta e validação. Operações de escrita e
destrutivas continuam desabilitadas, salvo quando o servidor MCP foi iniciado
com `NETBOX_MCP_ALLOW_MUTATIONS=1` ou `--allow-mutations`. O dry-run de uma
ferramenta de plugin executa os GETs ao vivo necessários para descobrir e
validar o manifesto atual, mas nunca envia a operação de destino anunciada.

A descoberta e o envio usam o transporte limitado da ponte no SDK: redirects
HTTP nunca são seguidos, respostas `3xx` falham de forma segura, a descoberta
ignora o cache HTTP comum e seu stale-if-error, `Content-Length` é verificado
antes da leitura e bytes descompactados/em chunks são contados durante o stream.
Assim, um anúncio ou tool removido não continua autorizado por cache antigo e
um redirect não encaminha uma mutação para fora do caminho fixo do plugin.

## Checklist para autores de plugins

1. Reutilize um endpoint DRF existente com gate de permissões para a operação.
2. Adicione uma view de manifesto somente leitura em
   `/api/plugins/<plugin>/mcp/`.
3. Anuncie esse caminho exato na raiz da API do plugin com versão de schema `1`.
4. Mantenha todos os caminhos de destino fixos e locais ao plugin; modele
   parâmetros no schema estrito de entrada, não em templates de caminho.
5. Faça método, efeito, anotações e serializer do endpoint coincidirem.
6. Adicione testes de contrato para anúncio, manifesto, permissões, schemas de
   requisição/resposta e ausência de uma pilha MCP ou credencial paralela.

Manifestos pertencem ao repositório do plugin produtor e devem ser validados
contra a versão publicada do SDK. O fixture do SDK é deliberadamente um
descritor genérico; ele não é o snapshot canônico de payload do Proxbox nem de
qualquer outro plugin.
