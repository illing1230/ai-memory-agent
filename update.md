# 업데이트 기록

## 2026-03-04

### 1. 로그인 페이지 개선
**파일:** `frontend/src/features/auth/components/LoginForm.tsx`

- 테스트 계정 이메일을 `hy.joo@samsung.com`으로 변경
- 비밀번호를 환경변수 `VITE_TEST_PASSWORD`에서 가져오도록 수정
- Mattermost 로그인 버튼 삭제
- 외부인증 글자 삭제
- 데모용 테스트 계정 문구 삭제

### 2. Docker Compose 구성
**파일:** `docker-compose.yml`

- Qdrant 서비스에 profile 추가 (`services.qdrant.profiles`)
- `QDRANT_URL` 환경변수로 구성 가능하도록 수정
- frontend+backend만 실행 가능하도록 설정

### 3. SDK Demo 스크립트 404 오류 수정
**파일:** `src/scripts/demo_agent_sdk.py`

- `get_api_key_from_db()` 함수에서 API 키로 조회하도록 수정
- `send_message()` 대신 `send_memory()` 사용하도록 변경
- 에이전트 이름을 동적으로 사용하도록 수정

### 4. Agent Dashboard 데이터 표시 수정
**파일:** `src/agent/repository.py`, `frontend/src/features/admin/components/AgentDashboardTab.tsx`, `frontend/src/types/common.types.ts`

- `get_all_instances_stats()`에서 `data_count` 필드 추가
- 모든 데이터 타입(memory, message, log) 카운트 포함
- 표시: "데이터: {data_count}개 (메모리: {memory_count}개)"

### 5. Agent 메모리 소유권 수정
**파일:** `src/agent/service.py`

- `_convert_to_memory()`에서 에이전트 인스턴스의 `owner_id`를 메모리 소유자로 사용
- SDK에서 전송한 메모리가 에이전트 소유자에게 제대로 할당되도록 수정

### 6. 대화형 Agent SDK 데모 생성
**파일:** `src/scripts/agent_sdk_demo.py` (신규)

- AI Memory Agent SDK를 대화형으로 테스트할 수 있는 데모 스크립트 생성
- 명령어 기반 상호작용 (`/health`, `/memory`, `/message`, `/log`, `/data`, `/sources`, `/search`, `/agent`, `/clear`, `/help`, `/exit`)
- API 키 입력 방식: 명령줄 인자 > 환경 변수 > 대화형 입력 > DB 첫 번째 활성 Agent

### 7. AI 대화 모드 추가
**파일:** `src/scripts/agent_sdk_demo.py`, `.env`

- `ENABLE_AI_CHAT=true` 설정 시 AI와 대화 가능
- `.env` 파일의 LLM 설정 사용 (`LLM_URL`, `LLM_API_KEY`, `LLM_MODEL`)
- `SAVE_AI_RESPONSE=true` 설정 시 AI 응답도 메모리에 저장

### 8. AI 응답 메모리 저장 기능
**파일:** `src/scripts/agent_sdk_demo.py`

- AI와 대화할 때 사용자 메시지와 AI 응답 모두 메모리로 저장
- Frontend 메모리 관리 페이지의 에이전트 탭에서 확인 가능

### 9. 환경변수 설정
**파일:** `.env`, `frontend/vite-env.d.ts`

- `VITE_TEST_PASSWORD=1234qwer` 추가
- TypeScript 타입 정의 추가
- `ENABLE_AI_CHAT=true`, `SAVE_AI_RESPONSE=true` 추가

## 사용 방법

### Agent SDK 데모 실행 (메모리 전송 모드)
```bash
cd ai-memory-agent
python -m src.scripts.agent_sdk_demo
```

### Agent SDK 데모 실행 (AI 대화 모드)
```bash
cd ai-memory-agent
python -m src.scripts.agent_sdk_demo
```
(ENV 파일에 `ENABLE_AI_CHAT=true` 설정되어 있음)

### API 키로 실행
```bash
python -m src.scripts.agent_sdk_demo --api-key sk_xxxxx
```

## 문제 해결

1. **SDK Demo 404 오류**: `agent_id`가 비어있던 문제를 API 키로 조회하여 해결
2. **Agent Dashboard 데이터 안 보임**: `data_count`를 포함하도록 수정
3. **Agent 메모리 소유권 문제**: 에이전트 인스턴스의 `owner_id`를 메모리 소유자로 사용
4. **TEST AGENT 메모리 안 보임**: SDK에서 `send_message()` 대신 `send_memory()` 사용