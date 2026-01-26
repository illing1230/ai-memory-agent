INFO:     127.0.0.1:42334 - "POST /api/v1/memories HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
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
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/http_proxy.py", line 316, in handle_async_request
    stream = await stream.start_tls(**kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/http11.py", line 376, in start_tls
    return await self._stream.start_tls(ssl_context, server_hostname, timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_backends/anyio.py", line 67, in start_tls
    with map_exceptions(exc_map):
         ~~~~~~~~~~~~~~^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/contextlib.py", line 162, in __exit__
    self.gen.throw(value)
    ~~~~~~~~~~~~~~^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_exceptions.py", line 14, in map_exceptions
    raise to_exc(exc) from exc
httpcore.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Basic Constraints of CA cert not marked critical (_ssl.c:1028)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/shared/providers/embedding/huggingface.py", line 49, in embed_batch
    response = await client.post(
               ^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpx/_client.py", line 1859, in post
    return await self.request(
           ^^^^^^^^^^^^^^^^^^^
    ...<13 lines>...
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpx/_client.py", line 1540, in request
    return await self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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
httpx.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Basic Constraints of CA cert not marked critical (_ssl.c:1028)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/uvicorn/protocols/http/httptools_impl.py", line 409, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.scope, self.receive, self.send
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/applications.py", line 1135, in __call__
    await super().__call__(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/applications.py", line 107, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/middleware/cors.py", line 93, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/middleware/cors.py", line 144, in simple_response
    await self.app(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/routing.py", line 716, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/routing.py", line 736, in app
    await route.handle(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/routing.py", line 290, in handle
    await self.app(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 115, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 101, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 355, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 243, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/memory/router.py", line 38, in create_memory
    return await service.create_memory(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<10 lines>...
    )
    ^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/memory/service.py", line 40, in create_memory
    vector = await embedding_provider.embed(content)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/shared/providers/embedding/huggingface.py", line 31, in embed
    results = await self.embed_batch([text])
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/shared/providers/embedding/huggingface.py", line 77, in embed_batch
    raise ProviderException("HuggingFace Embedding", str(e))
src.shared.exceptions.ProviderException: HuggingFace Embedding Provider 오류: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Basic Constraints of CA cert not marked critical (_ssl.c:1028)