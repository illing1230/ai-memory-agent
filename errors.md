========== 메모리 검색 시작 ==========
현재 채팅방 ID: b925ba6b-b282-4a47-b041-d3b32488b6d8
context_sources: {'memory': {'include_this_room': True, 'other_chat_rooms': [], 'include_personal': False, 'projects': [], 'departments': []}, 'rag': {'collections': [], 'filters': {}}}
memory_config: {'include_this_room': True, 'other_chat_rooms': [], 'include_personal': False, 'projects': [], 'departments': []}
other_chat_rooms: []

[1] 이 채팅방(b925ba6b-b282-4a47-b041-d3b32488b6d8) 메모리 검색 중...
    검색 결과: 1개
    - score: 0.904, payload: {'memory_id': '054acd89-5a2c-4908-a88c-ee4909e6fe3b', 'scope': 'chatroom', 'owner_id': '4cbcb120-e2f8-465d-82fe-4f5d613d90c0', 'chat_room_id': 'b925ba6b-b282-4a47-b041-d3b32488b6d8'}

[2] 다른 채팅방 검색 대상: []

========== 총 메모리 검색 결과: 1개 ==========
  - 오늘 불량은 새벽급방전이야... (score: 0.904)

INFO:     10.244.14.37:52432 - "POST /api/v1/chat-rooms/b925ba6b-b282-4a47-b041-d3b32488b6d8/messages HTTP/1.1" 500 Internal Server Error



api.ts:41 
 POST http://10.244.14.73:8000/api/v1/chat-rooms/b925ba6b-b282-4a47-b041-d3b32488b6d8/messages 500 (Internal Server Error)
request	@	api.ts:41
post	@	api.ts:96
sendMessage	@	chatApi.ts:68
mutationFn	@	useChat.ts:58
await in execute		
(anonymous)	@	ChatRoom.tsx:78
handleSend	@	MessageInput.tsx:83
handleKeyDown	@	MessageInput.tsx:107

ChatRoom.tsx:80 메시지 전송 실패: ApiError: OpenAI LLM Provider 오류: 
    at request (api.ts:59:11)