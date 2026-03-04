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

---
Demo Scenario

[1번 시나리오]
1. MChat 대화방에서 초대
2. 대화방에서 대화(오늘 점심은 회를 먹어야 겠다.)
3. ai에게 질문 @ai 오늘 점심 뭐 먹는다고 했지?
4. 연결 확인 - 지식 목록에 포함 되는지 


[1번 시나리오]
1. Agent 등록 프로세스(hy.joo)
 - Agent 등록 : 대화형 에이전트, 테스트를 위한 에이전트 생성
 - 인스턴스 생성 : TEST AGENT
 - 내 인스턴스 에서 API 확인(api key = sk_57cc1497ee8940baa708316cc6c6d341)
 
2. SDK 설치 및 사용 방법
 - pip 설치 : python -m src.scripts.agent_sdk_demo
 - demo_agent 실행 : python -m src.scripts.agent_sdk_demo --api-key sk_57cc1497ee8940baa708316cc6c6d341
 
[2번 시나리오]

1. 대화방 개설
2. 메시지 전송
	오늘 개발팀 주간 회의에서 결정된 사항을 공유드립니다.

	1. __Q3 목표 매출 상향__: 기존 120억에서 150억으로 상향 조정. 마케팅 팀과 협의하여 신규 광고 캠페� 즉시 실행.
	2. __신규 채용 승인__: 프론트엔드 개발자 3명 채용 확정. 인사팀에 JD 전달 완료, 다음주부터 채용 공고 시작.
	3. __A프로젝트 일정 변경__: 기존 3월 25일 출시일에서 2주 연기하여 4월 8일 출시로 변경. 테스트 기간 확보 필요.
	4. __B팀 협업 MOU 체결 예정__: B팀과 데이터 공급 계약 추진, 다달 초 MOU 체결 목표.
	5. __보안 감사 일정 확정__: 외부 보안 감사사 선정 완료, 다음달 15일부터 3일간 진행 예정.
	6. __출장비 정책 변경__: 일일 한도 10만원에서 15만원으로 상향. 숙박비 별도 지원, 영수증 필수 제출.
	7. __Qwen3.5-397B-FP8 모델 배포 공지__: H200 4장 사용하여 배포 완료. max-model-len: 131072 설정됨.

3. 개인적인 메시지 전송
	오늘 저녁에 회식 있습니다.
	회식 추천 받습니다.
	주호영님은 돼지고기를 좋아해요.
 
4. 새로운 대화방 개설
	@ai H200에 배포된 모델명이 뭐야?
	@ai 오늘 회식 일정이 별도로 있어?
	@ai 돼지 고기 좋아하는 사람이 있어?
	
	@ai 오늘 회의 요약해줘.
	// 문제점 : 한문장에 표현된 자료가 많은데 이걸 질문으로 가져올 경우 유사한 k개를 가져오는데, 너무 적게 가져옴.(개선 필요)
5. 대화방에 developer 초대

6. developer@samsung.com 계정으로 로그인
  - 지식 목록 확인
  - 질문
    . @ai 오늘 회식 일정 있어? (사용자 식별 확인)
	. @ai 다른 사람들 회식 일정 알려줘
	. @ai 모델 배포 공지된 내용 알려줘
	

