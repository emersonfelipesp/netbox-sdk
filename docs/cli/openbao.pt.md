# CLI OpenBao

`nbx openbao` expõe o contrato mantido de `netbox-openbao` sem acesso direto ao
OpenBao. `nbx openbao resources` imprime o catálogo sem criar um cliente. As
coleções usam somente as operações CRUD e em lote permitidas pelo contrato.

```bash
nbx openbao credentials list -q policy_id=4
nbx openbao credentials create \
  --body-json '{"name":"router","generate_ssh_key":true,"ssh_key_type":"ed25519"}' \
  --confirm
nbx openbao actions credential-rotate --id 12 \
  --body-file rotation.json --confirm
```

Toda mutação e toda leitura que retorna material exige `--confirm` antes da
criação do cliente. As
opções repetidas `--query`, `--header` e `--path-param` preservam o formato do
transporte. A saída com segredos é deliberadamente de uso único no terminal:
não a envie para logs, histórico do shell, armazenamento compartilhado ou
artefatos de CI.

Snapshots usam comandos dedicados e limitados:

```bash
nbx openbao snapshot download --id 3 --output cluster.snap --max-bytes 536870912 --confirm
nbx openbao snapshot upload --id 3 --input cluster.snap \
  --reason "recuperação de desastre" --confirmation "RESTORE SNAPSHOT primary" \
  --openbao-cluster-id raft-cluster-a --raft-index 17 --confirm
```

O download cria o destino atomicamente com modo `0600` e recusa sobrescrever um
caminho existente. O upload abre o arquivo sem seguir links simbólicos, valida o
descritor e o limite de bytes e envia os quatro cabeçalhos obrigatórios a partir
das opções tipadas. Não há repetição
automática. Uma mutação com falha pode ter sido concluída; confira o estado
autoritativo do plugin antes de tentar novamente.
