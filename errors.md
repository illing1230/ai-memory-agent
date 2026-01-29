(base) hy.joo@nautilus:~/2026/gitprojects/ai-memory-agent$ python -m src.main
INFO:     Will watch for changes in these directories: ['/home/hy.joo/2026/gitprojects/ai-memory-agent']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [3146618] using WatchFiles
INFO:     Started server process [3146647]
INFO:     Waiting for application startup.
✅ SQLite 데이터베이스 초기화 완료: data/sqlite/memory.db
ERROR:    Traceback (most recent call last):
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpx/_transports/default.py", line 101, in map_httpcore_exceptions
    yield
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpx/_transports/default.py", line 394, in handle_async_request
    resp = await self._pool.handle_async_request(req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/connection_pool.py", line 256, in handle_async_request
    raise exc from None
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/connection_pool.py", line 236, in handle_async_request
    response = await connection.handle_async_request(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        pool_request.request
        ^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/http_proxy.py", line 206, in handle_async_request
    return await self._connection.handle_async_request(proxy_request)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/connection.py", line 103, in handle_async_request
    return await self._connection.handle_async_request(request)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/http11.py", line 136, in handle_async_request
    raise exc
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/http11.py", line 106, in handle_async_request
    ) = await self._receive_response_headers(**kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/http11.py", line 177, in _receive_response_headers
    event = await self._receive_event(timeout=timeout)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/http11.py", line 231, in _receive_event
    raise RemoteProtocolError(msg)
httpcore.RemoteProtocolError: Server disconnected without sending a response.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/qdrant_client/http/api_client.py", line 223, in send_inner
    response = await self._async_client.send(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpx/_client.py", line 1629, in send
    response = await self._send_handling_auth(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<4 lines>...
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpx/_client.py", line 1657, in _send_handling_auth
    response = await self._send_handling_redirects(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpx/_client.py", line 1694, in _send_handling_redirects
    response = await self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpx/_client.py", line 1730, in _send_single_request
    response = await transport.handle_async_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpx/_transports/default.py", line 393, in handle_async_request
    with map_httpcore_exceptions():
         ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/hy.joo/miniconda3/lib/python3.13/contextlib.py", line 162, in __exit__
    self.gen.throw(value)
    ~~~~~~~~~~~~~~^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpx/_transports/default.py", line 118, in map_httpcore_exceptions
    raise mapped_exc(message) from exc
httpx.RemoteProtocolError: Server disconnected without sending a response.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/routing.py", line 694, in lifespan
    async with self.lifespan_context(app) as maybe_state:
               ~~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/contextlib.py", line 214, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 153, in merged_lifespan
    async with original_context(app) as maybe_original_state:
               ~~~~~~~~~~~~~~~~^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/contextlib.py", line 214, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 153, in merged_lifespan
    async with original_context(app) as maybe_original_state:
               ~~~~~~~~~~~~~~~~^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/contextlib.py", line 214, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 153, in merged_lifespan
    async with original_context(app) as maybe_original_state:
               ~~~~~~~~~~~~~~~~^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/contextlib.py", line 214, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 153, in merged_lifespan
    async with original_context(app) as maybe_original_state:
               ~~~~~~~~~~~~~~~~^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/contextlib.py", line 214, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 153, in merged_lifespan
    async with original_context(app) as maybe_original_state:
               ~~~~~~~~~~~~~~~~^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/contextlib.py", line 214, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 153, in merged_lifespan
    async with original_context(app) as maybe_original_state:
               ~~~~~~~~~~~~~~~~^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/contextlib.py", line 214, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/main.py", line 21, in lifespan
    await init_vector_store()
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/shared/vector_store.py", line 44, in init_vector_store
    await _qdrant_client.create_collection(
    ...<5 lines>...
    )
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/qdrant_client/async_qdrant_client.py", line 1635, in create_collection
    return await self._client.create_collection(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<16 lines>...
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/qdrant_client/async_qdrant_remote.py", line 1868, in create_collection
    await self.http.collections_api.create_collection(
    ...<3 lines>...
    )
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/qdrant_client/http/api/collections_api.py", line 219, in create_collection
    return await self._build_for_create_collection(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/qdrant_client/http/api_client.py", line 184, in request
    return await self.send(request, type_)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/qdrant_client/http/api_client.py", line 201, in send
    response = await self.middleware(request, self.send_inner)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/qdrant_client/http/api_client.py", line 245, in __call__
    return await call_next(request)
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/qdrant_client/http/api_client.py", line 225, in send_inner
    raise ResponseHandlingException(e)
qdrant_client.http.exceptions.ResponseHandlingException: Server disconnected without sending a response.

ERROR:    Application startup failed. Exiting.