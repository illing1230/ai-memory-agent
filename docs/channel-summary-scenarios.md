# 채널 대화 자동 요약 - 시나리오별 동작 흐름

## 1. 자동 요약 (스케줄러)

```
서버 시작
  │
  ├─ .env: MCHAT_SUMMARY_ENABLED=true
  │
  ▼
worker.py: start_mchat_worker()
  │
  ├─ start_summary_scheduler(client, db, bot_user_id)
  │   └─ 로그: "Summary scheduler started"
  │
  ▼
summary_scheduler_loop()  ── 10분마다 폴링 ──┐
  │                                           │
  ▼                                           │
  DB 조회: sync_enabled=1 AND summary_enabled=1 채널 목록
  │
  ├─ Town Square (interval: 24h)
  │   ├─ 마지막 요약: 어제 09:00
  │   ├─ 현재: 오늘 09:10 → 경과 24h10m ≥ 24h ✅ 실행!
  │   │
  │   ▼
  │   summarize_channel()
  │   │
  │   ├─ 1) get_posts_since(since=어제09:00)
  │   │     └─ Mattermost REST API: GET /api/v4/channels/{id}/posts?since=...
  │   │     └─ 봇 메시지 필터링 → 23건 남음
  │   │
  │   ├─ 2) resolve_usernames()
  │   │     └─ user_id → @이검사, @최개발, @박관리, @김대리, @정기획
  │   │
  │   ├─ 3) generate_chunked_summary()
  │   │     └─ 23건 < 50 → 단일 청크
  │   │     └─ LLM 호출 (Claude) → 요약 텍스트 생성
  │   │
  │   ├─ 4) format_summary_post() → 마크다운 생성
  │   │
  │   ├─ 5) client.create_post() → 채널에 자동 포스팅
  │   │     ┌──────────────────────────────────────────┐
  │   │     │ ## :memo: 채널 대화 요약                    │
  │   │     │ **채널**: Town Square                      │
  │   │     │ **기간**: 2026-02-21 09:00 ~ 2026-02-22 09:00 │
  │   │     │ **메시지 수**: 23건 | **참여자**: 5명         │
  │   │     │ ---                                        │
  │   │     │ **주요 논의 주제**                           │
  │   │     │ - PLM 시스템 테스트 자동화 진행 상황          │
  │   │     │ - API 마이그레이션 일정 조율                  │
  │   │     │                                            │
  │   │     │ **결정 사항**                               │
  │   │     │ - 다음주 수요일까지 테스트 커버리지 80% 달성   │
  │   │     │                                            │
  │   │     │ **액션 아이템**                              │
  │   │     │ - @이검사: 테스트 리포트 작성 (금요일까지)     │
  │   │     │ - @최개발: API v2 스펙 문서 업데이트          │
  │   │     │                                            │
  │   │     │ **주요 멘션**                               │
  │   │     │ - 프로젝트: MemGate, PLM                    │
  │   │     │ - 일정: 3월 릴리즈                          │
  │   │     │ ---                                        │
  │   │     │ _이 요약은 AI Memory Agent에 의해 자동 생성_ │
  │   │     └──────────────────────────────────────────┘
  │   │
  │   ├─ 6) MemoryPipeline.save() → chatroom 메모리 저장
  │   │     └─ "[채널 요약: Town Square] 주요 논의 주제..."
  │   │
  │   └─ 7) INSERT mchat_summary_log → 이력 기록
  │
  ├─ Dev Channel (interval: 12h)
  │   ├─ 마지막 요약: 6시간 전 → 경과 6h < 12h → 스킵
  │
  └─ asyncio.sleep(600) → 10분 후 다시 폴링 ─────────────┘
```

---

## 2. 수동 요약 (`@ai 요약`)

```
Mattermost 채널에서 사용자가 입력:

  ┌─────────────────────────────────┐
  │ @이검사: @ai 요약               │  ← 최근 24시간 (기본값)
  └─────────────────────────────────┘
  또는
  ┌─────────────────────────────────┐
  │ @이검사: @ai 요약 48시간         │  ← 최근 48시간
  └─────────────────────────────────┘

        │
        ▼
  WebSocket 이벤트 수신
        │
        ▼
  _should_respond() → "@ai" 포함 → True
        │
        ▼
  _handle_summary_command()
        │
        ├─ regex 매칭: r"@ai\s+요약(?:\s+(\d+)\s*시간)?"
        │   └─ 매칭 성공! hours = 48 (또는 기본 24)
        │
        ├─ ⏳ add_reaction("hourglass_flowing_sand")
        │     ┌──────────────────────────────┐
        │     │ @이검사: @ai 요약 48시간  ⏳   │
        │     └──────────────────────────────┘
        │
        ├─ trigger_summary_now(hours=48)
        │   └─ summarize_channel(since=48시간전, until=now)
        │       └─ (위 자동 요약과 동일한 파이프라인)
        │
        ├─ ✅ add_reaction("white_check_mark")
        │     ┌──────────────────────────────┐
        │     │ @이검사: @ai 요약 48시간  ⏳✅ │
        │     └──────────────────────────────┘
        │
        └─ return True → 일반 ChatService 처리 스킵
```

**메시지 없는 경우:**
```
  trigger_summary_now() → posts 0건 → None 반환
        │
        ▼
  client.create_post("최근 48시간 동안 요약할 메시지가 없습니다.")
```

---

## 3. Admin API로 채널 요약 활성화

```
1) 채널 목록 조회
   GET /api/v1/mchat/channels
   Authorization: Bearer <admin_token>

   Response:
   [
     {
       "id": "abc-123",
       "mchat_channel_id": "ch_townSquare",
       "mchat_channel_name": "Town Square",
       "sync_enabled": true,
       "summary_enabled": false,        ← 아직 비활성
       "summary_interval_hours": 24,
       ...
     }
   ]

2) 요약 활성화
   PUT /api/v1/mchat/channels/abc-123/summary
   Body: { "enabled": true }

   Response: { "summary_enabled": true }

3) 주기 변경 (12시간마다)
   PUT /api/v1/mchat/channels/abc-123/summary-interval
   Body: { "interval_hours": 12 }

   Response: { "summary_interval_hours": 12 }

4) 수동 트리거 (API)
   POST /api/v1/mchat/summary/trigger/ch_townSquare?hours=6

   Response: { "message": "요약 트리거됨 (최근 6시간)", "channel_id": "ch_townSquare" }
   → 백그라운드에서 요약 실행 → 채널에 포스팅

5) 요약 상태/이력 확인
   GET /api/v1/mchat/summary/status

   Response:
   {
     "scheduler_running": true,
     "enabled_channels": 2,
     "total_summaries": 15,
     "recent_summaries_24h": 3
   }

   GET /api/v1/mchat/summary/logs?limit=5

   Response:
   [
     {
       "id": "log-001",
       "channel_name": "Town Square",
       "period_start_ms": 1740200400000,
       "period_end_ms": 1740286800000,
       "message_count": 23,
       "participant_count": 5,
       "summary_content": "**주요 논의 주제**\n- PLM ...",
       "memory_id": "mem-xyz",
       "created_at": "2026-02-22 09:00:00"
     },
     ...
   ]
```

---

## 4. 대량 메시지 청크 분할 (50개 초과)

```
채널에 메시지 127건

chunk_posts(posts, chunk_size=50)
  ├─ Chunk 1: posts[0:50]    → generate_summary() → 부분요약 1
  ├─ Chunk 2: posts[50:100]  → generate_summary() → 부분요약 2
  └─ Chunk 3: posts[100:127] → generate_summary() → 부분요약 3

LLM 통합 요약:
  prompt: "다음 부분 요약들을 하나로 통합해주세요:
           [파트 1] ...
           [파트 2] ...
           [파트 3] ..."

  → 최종 통합 요약 생성
```

---

## 5. 메모리 활용 시나리오

```
요약이 메모리로 저장된 후:

  ┌─────────────────────────────────────┐
  │ @이검사: @ai 지난주 Town Square에서  │
  │          뭐 논의했었지?              │
  └─────────────────────────────────────┘

        │
        ▼
  ChatService → MemoryPipeline.search()
        │
        ├─ 벡터 검색: "[채널 요약: Town Square] ..." 메모리 히트
        │
        ▼
  AI 응답:
  "지난주 Town Square에서는 주로 PLM 시스템 테스트 자동화와
   API 마이그레이션 일정에 대해 논의했습니다.
   테스트 커버리지 80%를 수요일까지 달성하기로 했고,
   이검사님이 테스트 리포트, 최개발님이 API v2 스펙 업데이트를
   담당하기로 했습니다."
```
