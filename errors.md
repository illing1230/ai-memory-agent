(base) hy.joo@nautilus:~/2026/gitprojects/ai-memory-agent$ python -m src.mchat.worker
==================================================
Mchat Worker - AI Memory Agent 연동
==================================================
MCHAT_URL: https://mchat.mosaic.sec.samsung.net
MCHAT_ENABLED: True
✅ SQLite 데이터베이스 초기화 완료: data/sqlite/memory.db

[Bot 정보 조회]
Bot ID: wazzwxjmwidfurkjsdwyrycyyr
Username: hy.joo

[WebSocket 연결 시작]
메시지를 기다리는 중... (Ctrl+C로 종료)
[Mchat] Connecting to WebSocket: wss://mchat.mosaic.sec.samsung.net/api/v4/websocket
[Mchat] WebSocket connected!
[Mchat] Event: hello
[Mchat] Event: channel_viewed
        Data: {"event": "channel_viewed", "data": {"channel_id": "f1qcwq7m77di3pa3xu7ygzn54r"}, "broadcast": {"omit_users": null, "user_id": "wazzwxjmwidfurkjsdwyrycyyr", "channel_id": "", "team_id": "", "connectio
[Mchat] Event: posted
        Data: {"event": "posted", "data": {"channel_display_name": "@hy.joo", "channel_name": "wazzwxjmwidfurkjsdwyrycyyr__wazzwxjmwidfurkjsdwyrycyyr", "channel_type": "D", "post": "{\"id\":\"wbtg9a83xfykfbbeyia7pr

[새 메시지] @@hy.joo: 오늘 불량 5건 발생했어...
  [저장완료] room=396c81f0-e4ae-4598-8bac-cd0c4fff1416
[Mchat] Event: channel_viewed
        Data: {"event": "channel_viewed", "data": {"channel_id": "f1qcwq7m77di3pa3xu7ygzn54r"}, "broadcast": {"omit_users": null, "user_id": "wazzwxjmwidfurkjsdwyrycyyr", "channel_id": "", "team_id": "", "connectio
[Mchat] Event: posted
        Data: {"event": "posted", "data": {"channel_display_name": "@hy.joo", "channel_name": "wazzwxjmwidfurkjsdwyrycyyr__wazzwxjmwidfurkjsdwyrycyyr", "channel_type": "D", "post": "{\"id\":\"4357d3xidpd17874gsxxrw

[새 메시지] @@hy.joo: @ai 오늘 불량 몇건이야?...
  [오류] 'NoneType' object has no attribute 'get'
Traceback (most recent call last):
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/mchat/worker.py", line 203, in handle_message
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
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/chat/service.py", line 515, in _generate_ai_response
    relevant_memories = await self._search_relevant_memories(
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<4 lines>...
    )
    ^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/chat/service.py", line 560, in _search_relevant_memories
    memory_config = context_sources.get("memory", {})
                    ^^^^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'get'
[Mchat] Event: channel_viewed
        Data: {"event": "channel_viewed", "data": {"channel_id": "f1qcwq7m77di3pa3xu7ygzn54r"}, "broadcast": {"omit_users": null, "user_id": "wazzwxjmwidfurkjsdwyrycyyr", "channel_id": "", "team_id": "", "connectio