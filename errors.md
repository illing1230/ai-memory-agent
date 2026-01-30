[LLM] 요청 URL: http://10.244.11.119:30434/v1/chat/completions
[LLM] 모델: /data/Qwen3-32B
INFO:     10.244.14.37:60722 - "GET /api/v1/chat-rooms/b925ba6b-b282-4a47-b041-d3b32488b6d8/messages?limit=100 HTTP/1.1" 200 OK
[LLM] 예상치 못한 오류: ReadError: 
[LLM] Traceback: Traceback (most recent call last):
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
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/http11.py", line 217, in _receive_event
    data = await self._network_stream.read(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.READ_NUM_BYTES, timeout=timeout
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_backends/anyio.py", line 32, in read
    with map_exceptions(exc_map):
         ~~~~~~~~~~~~~~^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/contextlib.py", line 162, in __exit__
    self.gen.throw(value)
    ~~~~~~~~~~~~~~^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_exceptions.py", line 14, in map_exceptions
    raise to_exc(exc) from exc
httpcore.ReadError

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/shared/providers/llm/openai.py", line 89, in generate
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
httpx.ReadError

WebSocket error: ProviderException: OpenAI LLM Provider 오류: ReadError: 
WebSocket traceback: Traceback (most recent call last):
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
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/http11.py", line 217, in _receive_event
    data = await self._network_stream.read(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.READ_NUM_BYTES, timeout=timeout
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_backends/anyio.py", line 32, in read
    with map_exceptions(exc_map):
         ~~~~~~~~~~~~~~^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/contextlib.py", line 162, in __exit__
    self.gen.throw(value)
    ~~~~~~~~~~~~~~^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_exceptions.py", line 14, in map_exceptions
    raise to_exc(exc) from exc
httpcore.ReadError

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/shared/providers/llm/openai.py", line 89, in generate
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
httpx.ReadError

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/websocket/router.py", line 104, in websocket_chat
    result = await chat_service.send_message(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/chat/service.py", line 241, in send_message
    ai_response = await self._generate_ai_response(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/chat/service.py", line 534, in _generate_ai_response
    response = await llm_provider.generate(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<4 lines>...
    )
    ^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/shared/providers/llm/openai.py", line 139, in generate
    raise ProviderException("OpenAI LLM", f"{type(e).__name__}: {e}")
src.shared.exceptions.ProviderException: OpenAI LLM Provider 오류: ReadError: