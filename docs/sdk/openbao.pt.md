# SDK OpenBao

`netbox_sdk.openbao` é o contrato mantido do SDK para `netbox-openbao`. Ele
contém um inventário fixo das dez coleções REST do plugin e de todas as ações
personalizadas expostas pela API canônica. A descoberta dinâmica continua
disponível para plugins desconhecidos, mas não é a autoridade para esta
superfície sensível à segurança.

```python
from netbox_sdk.openbao import OpenBaoClient

openbao = OpenBaoClient(client)
await openbao.request_resource("credentials", "create", payload={
    "name": "router-admin",
    "policy": 4,
    "credential_type": "ssh-key",
    "generate_ssh_key": True,
    "ssh_key_type": "ed25519",
})
```

A geração de chave SSH no servidor faz parte da criação padrão de credenciais.
A chave privada continua sendo somente de escrita e não é representada por uma
ação separada. A rota `credential.quick-add-ssh` coordena a operação atômica.

Todas as requisições ignoram o cache. Respostas com material secreto devem ser
consumidas uma única vez e não podem ser registradas, persistidas ou incluídas
em mensagens de exceção. O SDK não repete essas operações automaticamente;
após uma falha de transporte, verifique o estado do servidor antes de repetir
uma mutação.

Snapshots Raft usam `download_snapshot()` e `upload_snapshot()`, com limites
explícitos de bytes e transporte `application/octet-stream`. O upload exige
`reason`, a `confirmation` exata, `openbao_cluster_id` e `configuration_index`,
que formam os quatro cabeçalhos obrigatórios da restauração. Rotas aninhadas
usam parâmetros nomeados restritos a um único segmento seguro. Permissões,
digests, confirmações, justificativas e validações do servidor continuam sendo
a autoridade final.
