========== 메모리 검색 시작 ==========
현재 채팅방 ID: b925ba6b-b282-4a47-b041-d3b32488b6d8
context_sources: {'memory': {'include_this_room': True, 'other_chat_rooms': ['75a09311-3629-48d1-850c-2051b92fb362', 'ff80af8f-b3b1-4c4b-a7e8-965d21b9b38e'], 'include_personal': False, 'projects': [], 'departments': []}, 'rag': {'collections': [], 'filters': {}}}
memory_config: {'include_this_room': True, 'other_chat_rooms': ['75a09311-3629-48d1-850c-2051b92fb362', 'ff80af8f-b3b1-4c4b-a7e8-965d21b9b38e'], 'include_personal': False, 'projects': [], 'departments': []}
other_chat_rooms: ['75a09311-3629-48d1-850c-2051b92fb362', 'ff80af8f-b3b1-4c4b-a7e8-965d21b9b38e']

[1] 이 채팅방(b925ba6b-b282-4a47-b041-d3b32488b6d8) 메모리 검색 중...
    검색 결과: 1개
    - score: 0.817, payload: {'memory_id': '054acd89-5a2c-4908-a88c-ee4909e6fe3b', 'scope': 'chatroom', 'owner_id': '4cbcb120-e2f8-465d-82fe-4f5d613d90c0', 'chat_room_id': 'b925ba6b-b282-4a47-b041-d3b32488b6d8'}

[2] 다른 채팅방 검색 대상: ['75a09311-3629-48d1-850c-2051b92fb362', 'ff80af8f-b3b1-4c4b-a7e8-965d21b9b38e']
    채팅방(75a09311-3629-48d1-850c-2051b92fb362) 검색 중...
    검색 결과: 1개
    - score: 0.835, payload: {'memory_id': '9e9f6ad8-75d6-44b1-bcd6-389e735ea347', 'scope': 'chatroom', 'owner_id': '4cbcb120-e2f8-465d-82fe-4f5d613d90c0', 'chat_room_id': '75a09311-3629-48d1-850c-2051b92fb362'}
    채팅방(ff80af8f-b3b1-4c4b-a7e8-965d21b9b38e) 검색 중...
    검색 결과: 1개
    - score: 0.801, payload: {'memory_id': '97c56cef-f8c6-4703-8b59-f5d867313387', 'scope': 'chatroom', 'owner_id': '4cbcb120-e2f8-465d-82fe-4f5d613d90c0', 'chat_room_id': 'ff80af8f-b3b1-4c4b-a7e8-965d21b9b38e'}

========== 총 메모리 검색 결과: 3개 ==========
  - 나는 커피를 좋아해... (score: 0.835)
  - 오늘 불량은 새벽급방전이야... (score: 0.817)
  - 오늘 날씨는 흐려... (score: 0.801)

[LLM] 요청 URL: http://10.244.11.119:30434/v1/chat/completions
[LLM] 모델: /data/Qwen3-32B
[LLM] 연결 오류: All connection attempts failed
WebSocket error: ProviderException: OpenAI LLM Provider 오류: 연결 실패: http://10.244.11.119:30434/v1 - All connection attempts failed
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
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/connection.py", line 101, in handle_async_request
    raise exc
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/connection.py", line 78, in handle_async_request
    stream = await self._connect(request)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_async/connection.py", line 124, in _connect
    stream = await self._network_backend.connect_tcp(**kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_backends/auto.py", line 31, in connect_tcp
    return await self._backend.connect_tcp(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<5 lines>...
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_backends/anyio.py", line 113, in connect_tcp
    with map_exceptions(exc_map):
         ~~~~~~~~~~~~~~^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/contextlib.py", line 162, in __exit__
    self.gen.throw(value)
    ~~~~~~~~~~~~~~^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/httpcore/_exceptions.py", line 14, in map_exceptions
    raise to_exc(exc) from exc
httpcore.ConnectError: All connection attempts failed

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/shared/providers/llm/openai.py", line 88, in generate
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
httpx.ConnectError: All connection attempts failed

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
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/shared/providers/llm/openai.py", line 127, in generate
    raise ProviderException("OpenAI LLM", f"연결 실패: {self.base_url} - {e}")
src.shared.exceptions.ProviderException: OpenAI LLM Provider 오류: 연결 실패: http://10.244.11.119:30434/v1 - All connection attempts failed