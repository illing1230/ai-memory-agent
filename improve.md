# 대화 개선 목록

## 개요
이 문서는 AI Memory Agent의 대화 기능 개선 사항을 정리한 것입니다.

---

## 1. 메모리 추출 안정화

### 문제
- SDK 방식과 백엔드 방식의 메모리 추출 로직이 달라서 불안정
- JSON 파싱 오류 발생
- await 누락으로 인한 비동기 처리 문제

### 해결
- SDK 방식으로 단순화 (JSON 파싱 제거)
- 단순한 텍스트 추출 방식 사용
- 상세한 에러 로깅 추가
- await 누락 수정

### 수정 파일
- `src/chat/service.py`
  - `_cmd_memory` 메서드
  - `_extract_and_save_memories` 메서드

---

## 2. 날짜 포함

### 문제
- 메모리에 날짜 정보가 없어서 시간적 맥락 파악 어려움
- "오늘", "내일" 등의 상대적 표현이 모호함

### 해결
- `/memory` 명령어: 현재 날짜를 LLM 프롬프트에 포함
- `_extract_and_save_memories`: AI 응답 후 자동 메모리 추출 시 날짜 포함
- 저장되는 메모리 예시: "오늘(2026년 2월 6일) 불량률은 12%입니다"

### 수정 파일
- `src/chat/service.py`
  - `_cmd_memory` 메서드
  - `_extract_and_save_memories` 메서드

---

## 3. gpt-oss-120b 모델 호환성

### 문제
- gpt-oss-120b 모델은 `content` 필드 대신 `reasoning_content` 필드에 응답을 반환
- 응답 길이가 0자로 표시되는 문제

### 해결
- `reasoning_content` 필드 처리 추가
- reasoning 모델 특성 지원
- `content`가 None이면 `reasoning_content`를 사용

### 수정 파일
- `src/shared/providers/llm/openai.py`
  - `generate` 메서드

---

## 4. 중복 체크 완화

### 문제
- 중복 체크 로직이 너무 엄격해서 저장하지도 않은 메시지가 건너뜀
- score_threshold 0.85로 낮아서 유사한 내용도 중복으로 간주

### 해결
- score_threshold: 0.85 → 0.95로 상향 (더 엄격한 중복 체크)
- 내용 일치도 확인 추가 (Jaccard 유사도)
- 내용이 90% 이상 동일한 경우에만 중복으로 간주

### 수정 파일
- `src/chat/service.py`
  - `_cmd_memory` 메서드
  - `_extract_and_save_memories` 메서드

---

## 5. 타임아웃 증가

### 문제
- 504 Gateway Timeout 오류 발생
- gpt-oss-120b 모델이 느려서 120초 타임아웃 부족

### 해결
- `generate` 메서드: 120초 → 300초로 증가
- `generate_stream` 메서드: 120초 → 300초로 증가

### 수정 파일
- `src/shared/providers/llm/openai.py`
  - `generate` 메서드
  - `generate_stream` 메서드

---

## 6. 스트리밍 응답

### 문제
- AI 응답이 한 번에 표시되어 사용자 경험 저하
- 긴 응답의 경우 대기 시간이 김

### 해결
- OpenAI/Anthropic Provider에 스트리밍 메서드 구현
- ChatService에서 스트리밍 응답 처리
- WebSocket으로 실시간 전송

### 수정 파일
- `src/shared/providers/llm/openai.py`
  - `generate_stream` 메서드 추가
- `src/shared/providers/llm/anthropic.py`
  - `generate_stream` 메서드 추가
- `src/chat/service.py`
  - `_generate_ai_response` 메서드

---

## 7. @ai 응답 속도 개선 ⭐

### 문제
- @ai 응답이 너무 느림
- AI 응답 생성 → Vector DB 저장 → 메모리 추출 → 모두 완료 후 반환
- 사용자가 응답을 받기까지 오래 걸림

### 해결
- AI 응답 즉시 반환
- Vector DB 저장과 메모리 추출은 백그라운드에서 비동기 처리
- 백그라운드 태스크 메서드 구현
- 추출된 메모리가 있으면 WebSocket으로 알림 전송

### 수정 파일
- `src/chat/service.py`
  - `_generate_ai_response` 메서드
  - `_save_ai_response_and_extract_memories` 메서드 추가
  - `send_message` 메서드

---

## 8. max_tokens 최적화

### 문제
- max_tokens 150으로 설정하면 응답이 잘림
- max_tokens 300으로 설정하면 충분하지 않음

### 해결
- max_tokens: 300 → 1000으로 증가
- 충분한 토큰을 사용하여 메모리 추출

### 수정 파일
- `src/chat/service.py`
  - `_cmd_memory` 메서드
  - `_extract_and_save_memories` 메서드

---

## 9. SDK 백그라운드 처리 적용

### 문제
- SDK의 message 메서드가 동기식으로 순차적으로 작동
- 사용자 메시지 저장 → 메모리 검색 → LLM 호출 → 응답 저장 → 반환
- 백엔드보다 응답이 느림

### 해결
- 저장 작업을 백그라운드 스레드로 처리
- AI 응답 즉시 반환
- 백엔드와 동일한 사용자 경험 제공

### 수정 파일
- `ai_memory_agent_sdk/agent.py`
  - `message` 메서드
  - `threading` import 추가

### 구현 방식
```python
def message(self, content: str) -> str:
    # 1. 대화 기록에 추가
    self._history.append({"role": "user", "content": content})
    
    # 2. 메모리 검색
    memory_context = self._search_memories(content)
    
    # 3. LLM 호출
    response = self._call_llm(messages)
    
    # 4. 응답 기록
    self._history.append({"role": "assistant", "content": response})
    
    # 5. 백그라운드에서 저장
    def save_in_background():
        self._safe_send("message", f"[user] {content}")
        self._safe_send("message", f"[assistant] {response}")
    
    thread = threading.Thread(target=save_in_background, daemon=True)
    thread.start()
    
    return response  # 즉시 반환
```

### 백엔드와 SDK의 차이

| 항목 | 백엔드 | SDK |
|------|--------|-----|
| 비동기 구현 | `asyncio.create_task()` | `threading.Thread` |
| API 인터페이스 | 비동기 (`async def`) | 동기 (`def`) |
| 알림 | WebSocket | 없음 |
| 사용 환경 | FastAPI (비동기 웹 프레임워크) | 일반 Python 앱 |

---

## 전체 수정 파일 목록

1. `src/chat/service.py`
   - 메모리 추출 안정화
   - 날짜 포함
   - 중복 체크 완화
   - @ai 응답 속도 개선
   - max_tokens 최적화

2. `src/shared/providers/llm/openai.py`
   - gpt-oss-120b 모델 호환성
   - 타임아웃 증가
   - 스트리밍 응답

3. `src/shared/providers/llm/anthropic.py`
   - 스트리밍 응답

4. `ai_memory_agent_sdk/agent.py`
   - SDK 백그라운드 처리 적용
   - threading import 추가

---

## 성능 개선 효과

### 응답 속도
- @ai 응답: 백그라운드 처리로 즉시 반환
- 스트리밍: 실시간 응답 표시

### 안정성
- 메모리 추출: SDK 방식으로 단순화하여 안정화
- 타임아웃: 300초로 증가하여 504 오류 방지
- 중복 체크: 정교한 로직으로 오탐지 감소

### 사용자 경험
- 날짜 포함: 시간적 맥락 파악 용이
- 스트리밍: 실시간 응답 표시
- WebSocket 알림: 메모리 추출 완료 알림

---

## 추가 제안

### 더 빠른 모델 사용
현재 `gpt-oss-120b` (120B 파라미터) 모델을 사용 중입니다. 더 빠른 응답이 필요하다면:

```bash
# 현재: gpt-oss-120b (120B 파라미터, 느림)
OPENAI_LLM_MODEL=/data/gpt-oss-120b

# 제안: Qwen3-32B (32B 파라미터, 약 4배 빠름)
OPENAI_LLM_MODEL=/data/qwen3-32b
```

### 메모리 추출 최적화
- 메모리 추출 빈도 조정 (매 응답 후 vs N개 메시지 후)
- 메모리 추출 품질 vs 속도 트레이드오프
- 사용자 피드백 기반 학습

---

## 참고

- SDK 방식: `ai_memory_agent_sdk/agent.py`
- 백엔드 방식: `src/chat/service.py`
- LLM Provider: `src/shared/providers/llm/`
