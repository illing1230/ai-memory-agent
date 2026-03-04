# AI Memory Agent 긴 메시지 처리 개선 계획

## 문제 현황
1. **Truncation 문제**: 1500자 초과 메시지는 단순 잘림 (정보 손실)
2. **컨텍스트 분리**: 연관된 정보가 여러 청크로 나뉘어 검색 시 누락
3. **검색 한계**: limit 파라미터로 인한 정보 조각화
4. **LLM 토큰 제한**: 복잡한 메시지 분석 한계

## 해결방안 로드맵

### Phase 1: 지능형 청킹 (Intelligent Chunking)
**목표**: 단순 자르기 → 의미 단위 분할

```python
class IntelligentChunker:
    def __init__(self, max_chunk_size=1500, overlap_size=150):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
    
    async def chunk_message(self, content: str) -> list[dict]:
        """메시지를 의미 단위로 분할"""
        # 1. 문단 단위 분할 (우선순위)
        paragraphs = content.split('\n\n')
        
        # 2. 문장 단위 분할 (문단이 너무 긴 경우)
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk + para) <= self.max_chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk.strip()))
                    # 오버랩 처리
                    overlap = current_chunk[-self.overlap_size:]
                    current_chunk = overlap + para + "\n\n"
                else:
                    # 문단 자체가 너무 긴 경우 문장 단위 분할
                    sentences = self._split_sentences(para)
                    chunks.extend(self._chunk_sentences(sentences))
        
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk.strip()))
            
        return chunks
    
    def _create_chunk(self, content: str, chunk_index: int = 0, total_chunks: int = 1):
        """청크 메타데이터 생성"""
        return {
            "content": content,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "length": len(content),
            "is_continuation": chunk_index > 0
        }
```

### Phase 2: 계층적 요약 (Hierarchical Summarization)  
**목표**: 긴 메시지 → 요약본 + 상세본 동시 저장

```python
class HierarchicalMemoryPipeline(MemoryPipeline):
    async def extract_and_save_long_message(
        self, 
        content: str, 
        user_id: str, 
        room: dict
    ):
        """긴 메시지 처리: 요약 + 청킹 + 연결"""
        
        # 1. 전체 요약 생성
        summary = await self._generate_summary(content)
        
        # 2. 의미 단위 청킹
        chunks = await self.chunker.chunk_message(content)
        
        # 3. 요약본 저장 (검색용)
        summary_memory = await self.save(
            content=f"[요약] {summary}",
            user_id=user_id,
            room_id=room["id"],
            category="fact", 
            importance="high"
        )
        
        # 4. 청크별 저장 + 요약본과 연결
        chunk_memories = []
        for i, chunk in enumerate(chunks):
            chunk_memory = await self.save(
                content=f"[{i+1}/{len(chunks)}] {chunk['content']}",
                user_id=user_id,
                room_id=room["id"],
                category="fact",
                importance="medium",
                metadata={
                    "parent_summary_id": summary_memory["id"],
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
            chunk_memories.append(chunk_memory)
            
        return summary_memory, chunk_memories

    async def _generate_summary(self, content: str) -> str:
        """LLM으로 핵심 요약 생성"""
        llm = get_llm_provider()
        prompt = f"""다음 긴 메시지의 핵심 정보를 3-5줄로 요약해주세요:

{content[:3000]}

핵심 요약:"""
        
        return await llm.generate(prompt, max_tokens=300)
```

### Phase 3: 연결형 검색 (Connected Search)
**목표**: 요약본 검색 → 연결된 청크들 자동 확장

```python
class ConnectedSearchPipeline:
    async def search_with_expansion(
        self, 
        query: str, 
        user_id: str, 
        limit: int = 20
    ):
        """요약 검색 → 청크 확장 검색"""
        
        # 1. 기본 벡터 + FTS 검색
        basic_results = await self.basic_search(query, user_id, limit//2)
        
        # 2. 요약 메모리 발견 시 연결된 청크들 확장
        expanded_results = []
        for result in basic_results:
            memory = result["memory"]
            
            if memory["content"].startswith("[요약]"):
                # 연결된 청크들 조회
                chunks = await self._get_connected_chunks(memory["id"])
                expanded_results.extend(chunks)
            else:
                expanded_results.append(result)
                
            # 청크인 경우 부모 요약 + 형제 청크들 조회
            if "parent_summary_id" in memory.get("metadata", {}):
                parent_and_siblings = await self._get_parent_and_siblings(memory)
                expanded_results.extend(parent_and_siblings)
        
        # 3. 중복 제거 + 점수 재계산
        return self._dedupe_and_rerank(expanded_results, query)
    
    async def _get_connected_chunks(self, summary_id: str):
        """요약본에 연결된 모든 청크 조회"""
        cursor = await self.memory_repo.db.execute("""
            SELECT * FROM memories 
            WHERE JSON_EXTRACT(metadata, '$.parent_summary_id') = ?
            ORDER BY JSON_EXTRACT(metadata, '$.chunk_index')
        """, (summary_id,))
        
        rows = await cursor.fetchall()
        return [{"memory": dict(row), "score": 0.8} for row in rows]
```

### Phase 4: 적응형 청킹 (Adaptive Chunking)
**목표**: 내용 유형별 맞춤형 청킹 전략

```python
class AdaptiveChunker:
    def __init__(self):
        self.strategies = {
            "code": CodeChunker(),
            "document": DocumentChunker(), 
            "conversation": ConversationChunker(),
            "data": DataChunker()
        }
    
    async def detect_and_chunk(self, content: str):
        """내용 유형 감지 후 적합한 전략 선택"""
        content_type = await self._detect_content_type(content)
        chunker = self.strategies.get(content_type, self.strategies["document"])
        return await chunker.chunk(content)
    
    async def _detect_content_type(self, content: str) -> str:
        """LLM으로 내용 유형 분류"""
        # 간단한 휴리스틱 + LLM 판정
        if "```" in content and ("def " in content or "function" in content):
            return "code"
        elif content.count('\n') > 20 and '|' in content:
            return "data" 
        elif ":" in content[:200] and content.count('\n') < 10:
            return "conversation"
        else:
            return "document"
```

### Phase 5: 성능 최적화
1. **배치 임베딩**: 청크들을 배치로 임베딩 처리
2. **캐싱**: 자주 검색되는 요약본 캐시
3. **인덱싱**: 청크 연결 관계 전용 인덱스
4. **압축**: 중요도 낮은 오래된 청크 압축 저장

## 구현 우선순위

### 1차 (즉시 구현 가능)
- [x] 현재 문제점 분석
- [ ] Phase 1: 지능형 청킹 구현
- [ ] Phase 2: 계층적 요약 구현  

### 2차 (기능 검증 후)
- [ ] Phase 3: 연결형 검색 구현
- [ ] 기존 메모리와의 호환성 테스트

### 3차 (최적화)
- [ ] Phase 4: 적응형 청킹
- [ ] Phase 5: 성능 최적화
- [ ] 메모리 통합/정리 자동화

## 예상 효과

### Before
```
긴 메시지 (5000자) → 1500자만 저장 → 나머지 3500자 손실 → 검색 시 누락
```

### After  
```
긴 메시지 (5000자) → 요약(200자) + 청크3개(1600자씩) → 모든 정보 보존 → 검색 시 요약→청크 확장
```

### 검색 정확도 개선
- 현재: 60-70% (정보 손실로 인한)
- 목표: 85-95% (계층적 검색으로)

## 다음 스텝

1. **Phase 1 구현** - 지능형 청킹부터 시작
2. **테스트 데이터셋** - 긴 메시지 샘플로 검증
3. **성능 벤치마크** - 기존 vs 개선 성능 비교
4. **점진적 배포** - 기존 기능 영향 최소화

이렇게 하면 긴 메시지도 완전히 보존하면서, 검색할 때 필요한 부분을 정확히 찾을 수 있을 거야! 🔥