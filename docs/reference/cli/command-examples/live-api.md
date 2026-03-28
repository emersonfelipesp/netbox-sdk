# Live API

## `nbx demo dcim devices list`

=== ":material-console: Command"

    ```bash
    nbx demo dcim devices list
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo dcim devices list
    ```

    ```text
    (empty)
    ```

<span class="nbx-badge nbx-badge--err">exit&nbsp;124</span> <span class="nbx-badge nbx-badge--neutral">60.045s</span>

---

## `nbx demo ipam prefixes list`

=== ":material-console: Command"

    ```bash
    nbx demo ipam prefixes list
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo ipam prefixes list
    ```

    ```text
    Error: Unexpected failure: Cannot connect to host demo.netbox.dev:443 ssl:default [Temporary failure in name resolution]. Please retry or check your configuration.
    
    --- stderr ---
    api request failed
    Traceback (most recent call last):
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 1562, in _create_direct_connection
        hosts = await self._resolve_host(host, port, traces=traces)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 1178, in _resolve_host
        return await asyncio.shield(resolved_host_task)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 1209, in _resolve_host_with_throttle
        addrs = await self._resolver.resolve(host, port, family=self._family)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/resolver.py", line 40, in resolve
        infos = await self._loop.getaddrinfo(
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ...<5 lines>...
        )
        ^
      File "/root/.local/share/uv/python/cpython-3.14.3-linux-x86_64-gnu/lib/python3.14/asyncio/base_events.py", line 936, in getaddrinfo
        return await self.run_in_executor(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
            None, getaddr_func, host, port, family, type, proto, flags)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/root/.local/share/uv/python/cpython-3.14.3-linux-x86_64-gnu/lib/python3.14/concurrent/futures/thread.py", line 86, in run
        result = ctx.run(self.task)
      File "/root/.local/share/uv/python/cpython-3.14.3-linux-x86_64-gnu/lib/python3.14/concurrent/futures/thread.py", line 73, in run
        return fn(*args, **kwargs)
      File "/root/.local/share/uv/python/cpython-3.14.3-linux-x86_64-gnu/lib/python3.14/socket.py", line 983, in getaddrinfo
        for res in _socket.getaddrinfo(host, port, family, type, proto, flags):
                   ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    socket.gaierror: [Errno -3] Temporary failure in name resolution
    
    The above exception was the direct cause of the following exception:
    
    Traceback (most recent call last):
      File "/root/nms/netbox-sdk/netbox_sdk/client.py", line 160, in request
        response = await self._request_once(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^
        ...<8 lines>...
        )
        ^
      File "/root/nms/netbox-sdk/netbox_sdk/client.py", line 238, in _request_once
        async with session.request(
                   ~~~~~~~~~~~~~~~^
            method=method.upper(),
            ^^^^^^^^^^^^^^^^^^^^^^
        ...<4 lines>...
            headers=req_headers,
            ^^^^^^^^^^^^^^^^^^^^
        ) as response:
        ^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/client.py", line 1510, in __aenter__
        self._resp: _RetType = await self._coro
                               ^^^^^^^^^^^^^^^^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/client.py", line 779, in _request
        resp = await handler(req)
               ^^^^^^^^^^^^^^^^^^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/client.py", line 734, in _connect_and_send_request
        conn = await self._connector.connect(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            req, traces=traces, timeout=real_timeout
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        )
        ^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 672, in connect
        proto = await self._create_connection(req, traces, timeout)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 1239, in _create_connection
        _, proto = await self._create_direct_connection(req, traces, timeout)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 1568, in _create_direct_connection
        raise ClientConnectorDNSError(req.connection_key, exc) from exc
    aiohttp.client_exceptions.ClientConnectorDNSError: Cannot connect to host demo.netbox.dev:443 ssl:default [Temporary failure in name resolution]
    ```

<span class="nbx-badge nbx-badge--err">exit&nbsp;1</span> <span class="nbx-badge nbx-badge--neutral">4.774s</span>

---

## `nbx demo dcim sites list`

=== ":material-console: Command"

    ```bash
    nbx demo dcim sites list
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo dcim sites list
    ```

    ```text
    (empty)
    ```

<span class="nbx-badge nbx-badge--err">exit&nbsp;124</span> <span class="nbx-badge nbx-badge--neutral">60.079s</span>

---
