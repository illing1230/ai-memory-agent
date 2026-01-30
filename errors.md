NFO:     10.244.14.37:54444 - "GET /api/v1/chat-rooms/b925ba6b-b282-4a47-b041-d3b32488b6d8/messages?limit=100 HTTP/1.1" 200 OK

========== 메모리 검색 시작 ==========
현재 채팅방 ID: b925ba6b-b282-4a47-b041-d3b32488b6d8
context_sources: {'memory': {'include_this_room': True, 'other_chat_rooms': ['75a09311-3629-48d1-850c-2051b92fb362', 'ff80af8f-b3b1-4c4b-a7e8-965d21b9b38e'], 'include_personal': False, 'projects': [], 'departments': []}, 'rag': {'collections': [], 'filters': {}}}
memory_config: {'include_this_room': True, 'other_chat_rooms': ['75a09311-3629-48d1-850c-2051b92fb362', 'ff80af8f-b3b1-4c4b-a7e8-965d21b9b38e'], 'include_personal': False, 'projects': [], 'departments': []}
other_chat_rooms: ['75a09311-3629-48d1-850c-2051b92fb362', 'ff80af8f-b3b1-4c4b-a7e8-965d21b9b38e']

[1] 이 채팅방(b925ba6b-b282-4a47-b041-d3b32488b6d8) 메모리 검색 중...
    검색 결과: 1개
    - score: 0.816, payload: {'memory_id': '054acd89-5a2c-4908-a88c-ee4909e6fe3b', 'scope': 'chatroom', 'owner_id': '4cbcb120-e2f8-465d-82fe-4f5d613d90c0', 'chat_room_id': 'b925ba6b-b282-4a47-b041-d3b32488b6d8'}

[2] 다른 채팅방 검색 대상: ['75a09311-3629-48d1-850c-2051b92fb362', 'ff80af8f-b3b1-4c4b-a7e8-965d21b9b38e']
    채팅방(75a09311-3629-48d1-850c-2051b92fb362) 검색 중...
    검색 결과: 1개
    - score: 0.841, payload: {'memory_id': '9e9f6ad8-75d6-44b1-bcd6-389e735ea347', 'scope': 'chatroom', 'owner_id': '4cbcb120-e2f8-465d-82fe-4f5d613d90c0', 'chat_room_id': '75a09311-3629-48d1-850c-2051b92fb362'}
    채팅방(ff80af8f-b3b1-4c4b-a7e8-965d21b9b38e) 검색 중...
    검색 결과: 1개
    - score: 0.805, payload: {'memory_id': '97c56cef-f8c6-4703-8b59-f5d867313387', 'scope': 'chatroom', 'owner_id': '4cbcb120-e2f8-465d-82fe-4f5d613d90c0', 'chat_room_id': 'ff80af8f-b3b1-4c4b-a7e8-965d21b9b38e'}

========== 총 메모리 검색 결과: 3개 ==========
  - 나는 커피를 좋아해... (score: 0.841)
  - 오늘 불량은 새벽급방전이야... (score: 0.816)
  - 오늘 날씨는 흐려... (score: 0.805)

[LLM] 요청 URL: https://dna.sec.samsung.net/k8s/qwen3-token/v1/chat/completions
[LLM] 모델: /data/Qwen3-32B
[LLM] 응답 상태: 405
[LLM] 에러 응답: <html>
<head><title>405 Not Allowed</title></head>
<body>
<center><h1>405 Not Allowed</h1></center>
<hr><center>nginx</center>
</body>
</html>

WebSocket error: ProviderException: OpenAI LLM Provider 오류: HTTP 405: <html>
<head><title>405 Not Allowed</title></head>
<body>
<center><h1>405 Not Allowed</h1></center>
<hr><center>nginx</center>
</body>
</html>

WebSocket traceback: Traceback (most recent call last):
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
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/shared/providers/llm/openai.py", line 99, in generate
    raise ProviderException("OpenAI LLM", f"HTTP {response.status_code}: {error_text[:200]}")
src.shared.exceptions.ProviderException: OpenAI LLM Provider 오류: HTTP 405: <html>
<head><title>405 Not Allowed</title></head>
<body>
<center><h1>405 Not Allowed</h1></center>
<hr><center>nginx</center>
</body>
</html>