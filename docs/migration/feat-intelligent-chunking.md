# feat/intelligent-chunking 브랜치 변경사항

> 기준: `main` 브랜치 대비 diff
> 날짜: 2026-03-04
> 커밋 3개:
> - `35689a4` feat: 지능형 청킹 구현 완료 🔥
> - `4218166` feat: Phase 2 계층적 메모리 구현 완료 🌟
> - `f30d88d` feat: Phase 3 적응형 청킹 + SDK Demo 완료 🌟

---

## 변경 요약

| 파일 | 상태 | 변경량 |
|------|------|--------|
| `CHUNKING_IMPROVEMENT_PLAN.md` | 🆕 신규 | +243줄 |
| `PHASE2_IMPROVEMENTS.md` | 🆕 신규 | +135줄 |
| `PHASE3_COMPLETE.md` | 🆕 신규 | +256줄 |
| `src/memory/adaptive.py` | 🆕 신규 | +692줄 |
| `src/memory/chunking.py` | 🆕 신규 | +395줄 |
| `src/memory/hierarchical.py` | 🆕 신규 | +580줄 |
| `src/memory/pipeline.py` | ✏️ 수정 | +285줄 / -14줄 |
| `src/scripts/interactive_demo.py` | 🆕 신규 | +474줄 |
| `tests/test_adaptive.py` | 🆕 신규 | +437줄 |
| `tests/test_chunking.py` | 🆕 신규 | +164줄 |
| `tests/test_hierarchical.py` | 🆕 신규 | +417줄 |
| **합계** | | **+4078줄 / -14줄** |

---

## 1. `CHUNKING_IMPROVEMENT_PLAN.md` (🆕 신규)

문서 파일. 전체 개선 계획서 (Phase 1~5 로드맵).

**→ 파일 전체를 새로 생성하면 됨.**

<details>
<summary>전체 내용 (243줄)</summary>

```markdown
# AI Memory Agent 긴 메시지 처리 개선 계획

## 문제 현황
1. **Truncation 문제**: 1500자 초과 메시지는 단순 잘림 (정보 손실)
2. **컨텍스트 분리**: 연관된 정보가 여러 청크로 나뉘어 검색 시 누락
3. **검색 한계**: limit 파라미터로 인한 정보 조각화
4. **LLM 토큰 제한**: 복잡한 메시지 분석 한계

## 해결방안 로드맵

### Phase 1: 지능형 청킹 (Intelligent Chunking)
**목표**: 단순 자르기 → 의미 단위 분할

class IntelligentChunker:
    def __init__(self, max_chunk_size=1500, overlap_size=150):
        ...
    async def chunk_message(self, content: str) -> list[dict]:
        # 문단 단위 → 문장 단위 분할 + 오버랩

### Phase 2: 계층적 요약 (Hierarchical Summarization)
**목표**: 긴 메시지 → 요약본 + 상세본 동시 저장

class HierarchicalMemoryPipeline(MemoryPipeline):
    async def extract_and_save_long_message(...)
        # 1. 전체 요약 생성
        # 2. 의미 단위 청킹
        # 3. 요약본 저장
        # 4. 청크별 저장 + 요약본 연결

### Phase 3: 연결형 검색 (Connected Search)
**목표**: 요약본 검색 → 연결된 청크들 자동 확장

### Phase 4: 적응형 청킹 (Adaptive Chunking)
**목표**: 내용 유형별 맞춤형 청킹 전략

### Phase 5: 성능 최적화
배치 임베딩, 캐싱, 인덱싱, 압축
```

</details>

---

## 2. `PHASE2_IMPROVEMENTS.md` (🆕 신규)

문서 파일. Phase 2 계층적 메모리 구현 완료 보고서.

**→ 파일 전체를 새로 생성하면 됨.**

---

## 3. `PHASE3_COMPLETE.md` (🆕 신규)

문서 파일. Phase 3 적응형 청킹 + SDK Demo 완료 보고서.

**→ 파일 전체를 새로 생성하면 됨.**

---

## 4. `src/memory/chunking.py` (🆕 신규, 395줄)

지능형 청킹 모듈. 핵심 클래스:

- **`ChunkMetadata`** (dataclass): chunk_index, total_chunks, length, is_continuation, overlap_start, overlap_end
- **`MessageChunk`** (dataclass): content, metadata, original_start, original_end
- **`IntelligentChunker`**: 메인 청킹 엔진
  - `chunk_message(content, preserve_structure)` → `List[MessageChunk]`
  - `_detect_content_type(content)` → "code" | "structured" | "natural"
  - `_chunk_natural_language()` → 문단→문장 순서 분할
  - `_chunk_code_content()` → 함수/클래스 단위 분할
  - `_chunk_structured_content()` → 섹션 구분자 기반 분할
  - `_add_overlaps()` → 청크간 오버랩 추가
- **`ContentTypeDetector`**: 내용 유형 감지 유틸리티

**→ `src/memory/chunking.py` 파일 전체를 새로 생성.**

---

## 5. `src/memory/adaptive.py` (🆕 신규, 692줄)

Phase 3 적응형 청킹 시스템. 핵심 클래스:

- **`ContentType`** (Enum): CODE, DOCUMENT, CONVERSATION, DATA, MIXED, NATURAL
- **`ContentAnalysis`** (dataclass): primary_type, confidence, sections, recommended_strategy, complexity_score, estimated_chunks
- **`SmartContentDetector`**: 지능형 내용 유형 감지기
  - 코드/문서/대화/데이터 패턴 정규식 매칭
  - `analyze(content)` → `ContentAnalysis`
- **`CodeChunker`**: 코드 전용 (함수/클래스 단위)
- **`DocumentChunker`**: 문서 전용 (섹션/헤더 단위)
- **`ConversationChunker`**: 대화 전용 (화자별/주제 변경)
- **`DataChunker`**: 데이터 전용 (테이블/JSON 구조 보존)
- **`AdaptiveChunker`**: 마스터 클래스 (유형 감지 → 전략 선택)
  - `chunk_message(content, preserve_structure)` → `List[MessageChunk]`
  - `_chunk_mixed_content()` → 코드블록/텍스트 분리 후 각각 청킹
- **`BatchEmbeddingProcessor`**: 배치 임베딩 처리기
  - `process_chunks(chunks)` → `List[Tuple[MessageChunk, List[float]]]`

**→ `src/memory/adaptive.py` 파일 전체를 새로 생성.**

---

## 6. `src/memory/hierarchical.py` (🆕 신규, 580줄)

계층적 메모리 관리 모듈. 핵심 클래스:

- **`HierarchicalMemoryPipeline`**: 계층적 저장
  - `extract_and_save_hierarchical(content, room, user_id, user_name, ...)` → `(summary_memory, chunk_memories)`
  - `_generate_comprehensive_summary(content, user_name)` → 200~500자 요약
  - `_save_summary_memory(...)` → 요약본 저장 (importance=high, metadata.type=summary)
  - `_save_linked_chunks(...)` → 청크들을 요약본과 연결 저장 (metadata.parent_summary_id)
  - `_extract_chunk_memories(...)` → LLM으로 각 청크에서 메모리 추출
  - `_save_chunk_memory(...)` → 중복 검사 + 저장

- **`HierarchicalSearchPipeline`**: 계층적 검색
  - `search_with_expansion(query, user_id, current_room_id, limit)` → 확장된 결과
  - 요약본 발견 시 `_get_linked_chunks(summary_id)` → 연결된 청크 자동 확장
  - 점수 조정: 요약본(원점수) > 연결 청크(×0.9) > 일반(원점수)

**→ `src/memory/hierarchical.py` 파일 전체를 새로 생성.**

---

## 7. `src/memory/pipeline.py` (✏️ 수정, +285/-14)

기존 파일 수정. 변경 내용:

### 7-1. import 추가 (상단)

**위치**: 기존 import 블록 끝 (`from src.config import get_settings` 뒤)

```python
# 추가할 import
from src.memory.chunking import IntelligentChunker, ContentTypeDetector
from src.memory.adaptive import AdaptiveChunker
from src.memory.hierarchical import HierarchicalMemoryPipeline, HierarchicalSearchPipeline
```

### 7-2. `MemoryPipeline.__init__()` 수정

기존 `__init__` 끝에 다음 블록 추가 (`self.settings = get_settings()` 뒤):

```python
        # 🌟 Phase 3: 적응형 청킹 시스템
        self.adaptive_chunker = AdaptiveChunker(
            max_chunk_size=1500,
            overlap_size=150,
            min_chunk_size=200
        )
        # 호환성을 위한 기존 청킹
        self.chunker = IntelligentChunker(
            max_chunk_size=1500,
            overlap_size=150,
            min_chunk_size=200
        )
        # 🔥 Phase 2: 계층적 메모리 파이프라인 (Phase 3 적응형 청킹 사용)
        self.hierarchical_pipeline = HierarchicalMemoryPipeline(
            memory_repo=memory_repo,
            entity_repo=self.entity_repo,
            chunker=self.adaptive_chunker,
            use_adaptive=True
        )
        self.hierarchical_search = HierarchicalSearchPipeline(memory_repo=memory_repo)
```

### 7-3. `search_memories_for_context()` 메서드 수정

**기존 코드 (제거):**
```python
        """컨텍스트 소스 기반 메모리 검색 (벡터 검색 → 배치 메타데이터 → 리랭킹)"""
        if context_sources is None:
            context_sources = {}

        memory_config = context_sources.get("memory", {})

        print(f"\n========== 메모리 검색 시작 ==========")
        print(f"현재 대화방 ID: {current_room_id}")
        print(f"memory_config: {memory_config}")

        embedding_provider = get_embedding_provider()
```

**새 코드 (교체):**
```python
        """🔥 Phase 2: 계층적 검색 우선 + 기존 검색 보완"""
        if context_sources is None:
            context_sources = {}

        memory_config = context_sources.get("memory", {})

        print(f"\n========== Phase 2 메모리 검색 시작 ==========")
        print(f"현재 대화방 ID: {current_room_id}")
        print(f"memory_config: {memory_config}")

        # 🌟 Step 0: 계층적 검색 우선 시도
        try:
            hierarchical_results = await self.hierarchical_search.search_with_expansion(
                query=query,
                user_id=user_id,
                current_room_id=current_room_id,
                limit=limit
            )
            
            if hierarchical_results:
                print(f"[계층적 검색] 성공: {len(hierarchical_results)}개 결과")
                
                # 접근 추적
                accessed_ids = [r["memory"]["id"] for r in hierarchical_results]
                if accessed_ids:
                    try:
                        await self.memory_repo.update_access(accessed_ids)
                    except Exception as e:
                        print(f"접근 추적 실패: {e}")
                
                return hierarchical_results
            else:
                print(f"[계층적 검색] 결과 없음, 기존 검색으로 fallback")
        except Exception as e:
            print(f"[계층적 검색] 실패, 기존 검색으로 fallback: {e}")

        # 🔄 Fallback: 기존 검색 로직
        print(f"[기존 검색] 시작")
        embedding_provider = get_embedding_provider()
```

### 7-4. 검색 결과 로그 변경

**기존:**
```python
        print(f"========== 총 메모리 검색 결과: {len(result)}개 ==========")
```

**변경:**
```python
        print(f"========== [기존 검색] 총 메모리 검색 결과: {len(result)}개 ==========")
```

### 7-5. `extract_and_save()` 메서드 대화 처리 부분 수정

기존의 대화 메시지 처리 로직을 대폭 변경:

**기존 (제거):**
```python
            # 사용자 메시지만 필터링 — content 문자열만 추출 (DB row dict 제거)
            MAX_MSG_LEN = 1500  # 개별 메시지 최대 길이
            MAX_TOTAL_LEN = 6000  # 전체 대화 최대 길이

            conv_for_extraction = []
            for msg in conversation:
                # ... content 추출 로직 ...
                if len(content) > MAX_MSG_LEN:
                    content = content[:MAX_MSG_LEN] + "... (이하 생략)"
                # 발신자 이름 포함
                sender = msg.get("user_name", "") if isinstance(msg, dict) else ""
                if not sender:
                    sender = msg.get("role", "user") if isinstance(msg, dict) else "user"
                conv_for_extraction.append({"sender": sender, "content": content})

            conversation_text = "\n".join(
                f"{m['sender']}: {m['content']}"
                for m in conv_for_extraction
            )
            if len(conversation_text) > MAX_TOTAL_LEN:
                conversation_text = conversation_text[:MAX_TOTAL_LEN] + "\n... (이하 생략)"
```

**새 코드 (교체):**
```python
            # 사용자 메시지만 필터링 — content 문자열만 추출 (DB row dict 제거)
            conv_for_extraction = []
            total_content_for_chunking = ""
            
            for msg in conversation:
                # ... content 추출 로직은 동일 ...
                # MAX_MSG_LEN 제거 (잘라내지 않음)
                    
                # 발신자 이름 포함
                sender = msg.get("user_name", "") if isinstance(msg, dict) else ""
                if not sender:
                    sender = msg.get("role", "user") if isinstance(msg, dict) else "user"
                
                # 원본 메시지를 수집 (지능형 청킹용)
                formatted_msg = f"{sender}: {content}"
                total_content_for_chunking += formatted_msg + "\n"
                
                conv_for_extraction.append({"sender": sender, "content": content})

            # 🔥 Phase 2: 계층적 처리 우선 시도
            print(f"[메모리 처리] 전체 대화 길이: {len(total_content_for_chunking)}자")
            
            # 긴 대화인 경우 계층적 처리 적용
            if len(total_content_for_chunking) > 6000:
                print(f"[메모리 처리] 긴 대화 감지! Phase 2 계층적 처리 적용")
                
                try:
                    # 🌟 계층적 요약 + 청킹 처리
                    summary_memory, chunk_memories = await self.hierarchical_pipeline.extract_and_save_hierarchical(
                        content=total_content_for_chunking,
                        room=room,
                        user_id=user_id,
                        user_name=user_name,
                        memory_context=memory_context,
                        threshold_length=6000
                    )
                    
                    if summary_memory and chunk_memories:
                        all_memories = [summary_memory] + chunk_memories
                        print(f"[계층적 처리] 성공! 요약본 1개 + 청크 {len(chunk_memories)}개 = 총 {len(all_memories)}개")
                        return all_memories
                    else:
                        print(f"[계층적 처리] 실패 또는 불필요, Phase 1 청킹으로 fallback")
                        
                except Exception as hierarchical_error:
                    print(f"[계층적 처리] 오류 발생, Phase 1 청킹으로 fallback: {hierarchical_error}")
                
                # 🔄 Phase 3 Fallback: 적응형 청킹 직접 사용
                try:
                    chunks = await self.adaptive_chunker.chunk_message(
                        content=total_content_for_chunking,
                        preserve_structure=True
                    )
                    
                    all_saved_memories = []
                    for i, chunk in enumerate(chunks):
                        chunk_memories = await self._extract_and_save_chunk(
                            chunk_content=chunk.content,
                            chunk_metadata=chunk.metadata,
                            room=room,
                            user_id=user_id,
                            user_name=user_name,
                            memory_context=memory_context,
                            current_date=current_date
                        )
                        all_saved_memories.extend(chunk_memories)
                    
                    return all_saved_memories
                    
                except Exception as chunking_error:
                    # Final Fallback: 기존 길이 제한 방식
                    conversation_text = total_content_for_chunking[:6000] + "\n... (모든 청킹 실패로 인한 자동 절단)"
            else:
                # 짧은 대화는 그대로 처리
                conversation_text = total_content_for_chunking.strip()
```

### 7-6. 새 메서드 추가: `_extract_and_save_chunk()`

`save()` 메서드 바로 위에 새 메서드 추가 (159줄):

```python
    async def _extract_and_save_chunk(
        self,
        chunk_content: str,
        chunk_metadata,
        room: dict[str, Any],
        user_id: str,
        user_name: str,
        memory_context: list[str] | None = None,
        current_date: str = None
    ) -> list[dict[str, Any]]:
        """단일 청크에서 메모리 추출 및 저장"""
        # 청크 정보를 포함한 system_prompt로 LLM 호출
        # JSON 파싱 → 메모리 저장
        # 청크 메타데이터(chunk_index, total_chunks) 포함
        # Fallback 처리 포함
```

**전체 구현은 diff의 `_extract_and_save_chunk` 메서드 참조 (약 159줄)**

---

## 8. `src/scripts/interactive_demo.py` (🆕 신규, 474줄)

SDK 인터랙티브 데모 스크립트. 커맨드라인 기반 메모리 테스트 도구.

**주요 기능:**
- `/save`, `/search`, `/memory`, `/ask`, `/test` 명령어
- Phase 3 적응형 청킹 자동 적용
- `ai_memory_agent_sdk.SyncClient` 사용

**→ `src/scripts/interactive_demo.py` 파일 전체를 새로 생성.**

---

## 9. `tests/test_chunking.py` (🆕 신규, 164줄)

Phase 1 지능형 청킹 테스트.

- `test_short_content()` — 짧은 내용 분할 안 됨 확인
- `test_long_natural_language()` — 긴 자연어 문단/문장 단위 분할
- `test_code_content()` — 코드 함수 단위 분할
- `test_content_type_detection()` — natural/code/structured 감지

**→ `tests/test_chunking.py` 파일 전체를 새로 생성.**

---

## 10. `tests/test_adaptive.py` (🆕 신규, 437줄)

Phase 3 적응형 청킹 테스트.

- `test_content_detection()` — 코드/문서/대화/데이터 유형 자동 분류
- `test_code_chunking()` — 함수/클래스 보존 확인
- `test_document_chunking()` — 섹션 구조 보존 확인
- `test_conversation_chunking()` — 화자별 보존 확인
- `test_adaptive_chunker()` — 혼합 내용 통합 테스트
- `test_batch_embedding()` — 배치 임베딩 처리 테스트

**→ `tests/test_adaptive.py` 파일 전체를 새로 생성.**

---

## 11. `tests/test_hierarchical.py` (🆕 신규, 417줄)

Phase 2 계층적 메모리 테스트.

- `test_summary_generation()` — 요약 생성 + 메타데이터 검증
- `test_hierarchical_search()` — 요약본→청크 확장 검색
- `test_integration()` — MemoryPipeline 통합 테스트
- Mock 클래스: `MockLLMProvider`, `MockEmbeddingProvider`
- 테스트용 인메모리 DB 설정 (`setup_test_db()`)

**→ `tests/test_hierarchical.py` 파일 전체를 새로 생성.**

---

## 적용 순서

1. 새 파일들 생성 (순서 중요):
   1. `src/memory/chunking.py`
   2. `src/memory/adaptive.py` (chunking.py 의존)
   3. `src/memory/hierarchical.py` (chunking.py, adaptive.py 의존)
2. `src/memory/pipeline.py` 수정 (7-1 ~ 7-6 순서대로)
3. 문서 파일 생성 (선택):
   - `CHUNKING_IMPROVEMENT_PLAN.md`
   - `PHASE2_IMPROVEMENTS.md`
   - `PHASE3_COMPLETE.md`
4. 데모/테스트 파일 생성 (선택):
   - `src/scripts/interactive_demo.py`
   - `tests/test_chunking.py`
   - `tests/test_adaptive.py`
   - `tests/test_hierarchical.py`
