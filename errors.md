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
        Data: {"event": "posted", "data": {"channel_display_name": "@hy.joo", "channel_name": "wazzwxjmwidfurkjsdwyrycyyr__wazzwxjmwidfurkjsdwyrycyyr", "channel_type": "D", "post": "{\"id\":\"ufof5ng4n7bsighjnge6cd

[새 메시지] @@hy.joo: 오늘 불량 5건 발생했어...
  [오류] UserRepository.create_user() got an unexpected keyword argument 'user_id'
Traceback (most recent call last):
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/mchat/worker.py", line 191, in handle_message
    agent_user_id = await get_or_create_agent_user(db, user_id, sender_name)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/mchat/worker.py", line 90, in get_or_create_agent_user
    user = await user_repo.create_user(
                 ~~~~~~~~~~~~~~~~~~~~~^
        user_id=mchat_user_id,
        ^^^^^^^^^^^^^^^^^^^^^^
        email=f"{mchat_username}@mchat.local",
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        name=mchat_username,
        ^^^^^^^^^^^^^^^^^^^^
    )
    ^
TypeError: UserRepository.create_user() got an unexpected keyword argument 'user_id'
[Mchat] Event: channel_viewed
        Data: {"event": "channel_viewed", "data": {"channel_id": "f1qcwq7m77di3pa3xu7ygzn54r"}, "broadcast": {"omit_users": null, "user_id": "wazzwxjmwidfurkjsdwyrycyyr", "channel_id": "", "team_id": "", "connectio
[Mchat] Event: posted
        Data: {"event": "posted", "data": {"channel_display_name": "@hy.joo", "channel_name": "wazzwxjmwidfurkjsdwyrycyyr__wazzwxjmwidfurkjsdwyrycyyr", "channel_type": "D", "post": "{\"id\":\"1as5esfp9jyrtji3wz66pw

[새 메시지] @@hy.joo: @ai 오늘 불량 몇건이야?...
  [오류] UserRepository.create_user() got an unexpected keyword argument 'user_id'
Traceback (most recent call last):
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/mchat/worker.py", line 191, in handle_message
    agent_user_id = await get_or_create_agent_user(db, user_id, sender_name)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/mchat/worker.py", line 90, in get_or_create_agent_user
    user = await user_repo.create_user(
                 ~~~~~~~~~~~~~~~~~~~~~^
        user_id=mchat_user_id,
        ^^^^^^^^^^^^^^^^^^^^^^
        email=f"{mchat_username}@mchat.local",
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        name=mchat_username,
        ^^^^^^^^^^^^^^^^^^^^
    )
    ^
TypeError: UserRepository.create_user() got an unexpected keyword argument 'user_id'
[Mchat] Event: channel_viewed
        Data: {"event": "channel_viewed", "data": {"channel_id": "f1qcwq7m77di3pa3xu7ygzn54r"}, "broadcast": {"omit_users": null, "user_id": "wazzwxjmwidfurkjsdwyrycyyr", "channel_id": "", "team_id": "", "connectio