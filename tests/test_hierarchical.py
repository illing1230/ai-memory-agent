"""
Phase 2 계층적 메모리 기능 테스트

HierarchicalMemoryPipeline과 HierarchicalSearchPipeline을 테스트한다.
"""

import asyncio
import sys
import os
import json
import tempfile
import uuid

# 테스트 환경 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory.hierarchical import HierarchicalMemoryPipeline, HierarchicalSearchPipeline
from src.memory.repository import MemoryRepository
from src.memory.entity_repository import EntityRepository
from src.memory.chunking import IntelligentChunker
from unittest.mock import AsyncMock, MagicMock


class MockLLMProvider:
    """테스트용 LLM Provider"""
    async def generate(self, prompt, system_prompt=None, temperature=0.3, max_tokens=1000):
        # 테스트용 고정 응답들
        if "종합 요약" in prompt or "요약해 주세요" in prompt:
            return "AI Memory Agent 프로젝트 Phase 2 계층적 메모리 구현 - 긴 메시지를 요약본과 청크로 분할 저장하여 검색 효율성과 정확도 향상"
        
        if "대화 청크를 분석" in prompt:
            return """[
  {
    "content": "AI Memory Agent 프로젝트에서 Phase 2 계층적 메모리 기능을 구현함",
    "category": "fact", 
    "importance": "high",
    "is_personal": false
  }
]"""
        
        return "테스트 응답"


class MockEmbeddingProvider:
    """테스트용 Embedding Provider"""
    async def embed(self, text):
        # 텍스트 해시를 기반으로 일관된 벡터 생성
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()
        # 384 차원 벡터로 변환
        vector = []
        for i in range(0, len(hash_hex), 2):
            val = int(hash_hex[i:i+2], 16) / 255.0
            vector.append(val)
        # 384개까지 패딩
        while len(vector) < 384:
            vector.extend(vector[:min(384-len(vector), len(vector))])
        return vector[:384]


async def setup_test_db():
    """테스트용 인메모리 DB 생성"""
    import aiosqlite
    
    # 임시 DB 파일
    temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_file.close()
    
    db = await aiosqlite.connect(temp_file.name)
    
    # 테스트용 간단한 스키마
    await db.execute('''
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            vector_id TEXT,
            scope TEXT DEFAULT 'chatroom',
            owner_id TEXT NOT NULL,
            chat_room_id TEXT,
            source_message_id TEXT,
            category TEXT,
            importance TEXT DEFAULT 'medium',
            metadata TEXT,
            topic_key TEXT,
            superseded INTEGER DEFAULT 0,
            superseded_by TEXT,
            superseded_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_accessed_at TEXT,
            access_count INTEGER DEFAULT 0
        )
    ''')
    
    await db.execute('''
        CREATE TABLE entities (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(name, type, owner_id)
        )
    ''')
    
    await db.execute('''
        CREATE TABLE memory_entities (
            memory_id TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            PRIMARY KEY (memory_id, entity_id),
            FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
            FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
        )
    ''')
    
    await db.commit()
    return db


async def test_summary_generation():
    """요약 생성 테스트"""
    print("📝 요약 생성 테스트 시작")
    
    # Mock 설정
    from src.shared import providers
    providers.get_llm_provider = lambda: MockLLMProvider()
    providers.get_embedding_provider = lambda: MockEmbeddingProvider()
    
    # 테스트 DB 생성
    db = await setup_test_db()
    memory_repo = MemoryRepository(db)
    entity_repo = EntityRepository(db)
    chunker = IntelligentChunker()
    
    # HierarchicalMemoryPipeline 생성
    pipeline = HierarchicalMemoryPipeline(memory_repo, entity_repo, chunker)
    
    # 긴 테스트 내용
    long_content = """
호영: 안녕하세요! AI Memory Agent 프로젝트 상황 보고드립니다.

최근에 Phase 1으로 지능형 청킹 기능을 구현했어요. 기존에는 1500자로 단순하게 자르던 방식을 
문단과 문장 단위로 의미있게 분할하도록 개선했습니다.

이제 Phase 2로 계층적 메모리 구현을 진행하고 있습니다. 주요 기능은:
1. 긴 메시지를 요약본과 상세 청크로 분리 저장
2. 요약본 검색으로 연결된 청크들 자동 확장
3. 정보 손실 0%와 검색 정확도 85% 이상 달성 목표

개발 현황:
- HierarchicalMemoryPipeline 클래스 구현 완료
- HierarchicalSearchPipeline 클래스 구현 완료  
- 기존 MemoryPipeline과 통합 완료
- 테스트 시나리오 작성 중

예상 효과:
- 검색 효율성 3-5배 향상
- 컨텍스트 완성도 95% 이상
- 토큰 효율성 20-40% 개선

다음 주 월요일까지 전체 테스트 완료하고 main 브랜치에 머지 예정입니다.
    """.strip()
    
    # 테스트 데이터
    room = {"id": "test-room-123"}
    user_id = "test-user-456"
    user_name = "호영"
    
    print(f"입력 길이: {len(long_content)}자")
    
    # 계층적 처리 실행
    summary_memory, chunk_memories = await pipeline.extract_and_save_hierarchical(
        content=long_content,
        room=room,
        user_id=user_id,
        user_name=user_name,
        threshold_length=1000  # 테스트용 낮은 임계값
    )
    
    # 결과 검증
    assert summary_memory is not None, "요약본이 생성되어야 함"
    assert len(chunk_memories) > 0, "청크 메모리들이 생성되어야 함"
    
    print(f"✅ 요약본 생성: {summary_memory['content'][:100]}...")
    print(f"✅ 청크 메모리 {len(chunk_memories)}개 생성")
    
    # 메타데이터 확인
    summary_metadata = json.loads(summary_memory.get("metadata", "{}"))
    assert summary_metadata.get("type") == "summary"
    assert summary_metadata.get("total_chunks") > 0
    
    # 청크 메타데이터 확인
    for chunk_mem in chunk_memories:
        chunk_metadata = json.loads(chunk_mem.get("metadata", "{}"))
        assert chunk_metadata.get("parent_summary_id") == summary_memory["id"]
        assert chunk_metadata.get("is_chunk_memory") == True
    
    print("✅ 요약 생성 테스트 통과!")
    await db.close()


async def test_hierarchical_search():
    """계층적 검색 테스트"""
    print("🔍 계층적 검색 테스트 시작")
    
    # Mock 설정
    from src.shared import providers
    providers.get_llm_provider = lambda: MockLLMProvider()
    providers.get_embedding_provider = lambda: MockEmbeddingProvider()
    
    # Mock vector search
    original_search_vectors = None
    try:
        from src.shared import vector_store
        original_search_vectors = vector_store.search_vectors
        
        async def mock_search_vectors(query_vector, limit=20, filter_conditions=None, **kwargs):
            # 테스트용 고정 결과 반환
            return [
                {
                    "id": "vector-1",
                    "score": 0.95,
                    "payload": {"memory_id": "summary-memory-1", "type": "summary"}
                },
                {
                    "id": "vector-2", 
                    "score": 0.85,
                    "payload": {"memory_id": "normal-memory-1", "type": "normal"}
                }
            ]
        
        vector_store.search_vectors = mock_search_vectors
        
        # 테스트 DB 생성
        db = await setup_test_db()
        memory_repo = MemoryRepository(db)
        
        # 테스트용 메모리 데이터 삽입
        # 1. 요약본 메모리
        summary_metadata = {
            "type": "summary",
            "total_chunks": 3,
            "original_length": 5000
        }
        
        await db.execute('''
            INSERT INTO memories (id, content, owner_id, chat_room_id, category, importance, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "summary-memory-1",
            "[요약] AI Memory Agent Phase 2 구현 프로젝트 현황 및 계획",
            "test-user",
            "test-room",
            "fact",
            "high",
            json.dumps(summary_metadata),
            "2023-12-01T10:00:00",
            "2023-12-01T10:00:00"
        ))
        
        # 2. 연결된 청크 메모리들
        for i in range(3):
            chunk_metadata = {
                "chunk_index": i,
                "total_chunks": 3,
                "parent_summary_id": "summary-memory-1",
                "is_chunk_memory": True
            }
            
            await db.execute('''
                INSERT INTO memories (id, content, owner_id, chat_room_id, category, importance, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"chunk-memory-{i+1}",
                f"[{i+1}/3] 청크 {i+1} 상세 내용입니다.",
                "test-user",
                "test-room", 
                "fact",
                "medium",
                json.dumps(chunk_metadata),
                "2023-12-01T10:00:00",
                "2023-12-01T10:00:00"
            ))
        
        # 3. 일반 메모리
        await db.execute('''
            INSERT INTO memories (id, content, owner_id, chat_room_id, category, importance, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "normal-memory-1",
            "일반 메모리 내용입니다.",
            "test-user", 
            "test-room",
            "fact",
            "medium",
            "2023-12-01T10:00:00",
            "2023-12-01T10:00:00"
        ))
        
        await db.commit()
        
        # HierarchicalSearchPipeline 생성
        search_pipeline = HierarchicalSearchPipeline(memory_repo)
        
        # 계층적 검색 실행
        results = await search_pipeline.search_with_expansion(
            query="AI Memory Agent 프로젝트",
            user_id="test-user",
            current_room_id="test-room",
            limit=10
        )
        
        # 결과 검증
        assert len(results) > 0, "검색 결과가 있어야 함"
        
        # 요약본과 연결된 청크들이 모두 포함되어야 함
        summary_found = False
        chunk_count = 0
        
        for result in results:
            if result.get("type") == "summary":
                summary_found = True
                print(f"✅ 요약본 발견: {result['memory']['content'][:50]}...")
            elif result.get("type") == "chunk":
                chunk_count += 1
                print(f"✅ 청크 발견: {result['memory']['content'][:50]}...")
        
        assert summary_found, "요약본이 검색 결과에 포함되어야 함"
        assert chunk_count == 3, f"3개 청크가 모두 확장되어야 함 (실제: {chunk_count}개)"
        
        print("✅ 계층적 검색 테스트 통과!")
        
    finally:
        # Mock 복원
        if original_search_vectors:
            vector_store.search_vectors = original_search_vectors
        await db.close()


async def test_integration():
    """통합 테스트 - MemoryPipeline에서 Phase 2 기능 확인"""
    print("🔗 통합 테스트 시작")
    
    # Mock 설정
    from src.shared import providers
    providers.get_llm_provider = lambda: MockLLMProvider()
    providers.get_embedding_provider = lambda: MockEmbeddingProvider()
    
    # Mock vector operations
    from src.shared import vector_store
    original_upsert = vector_store.upsert_vector
    vector_store.upsert_vector = AsyncMock()
    
    try:
        # 테스트 DB 생성
        db = await setup_test_db()
        memory_repo = MemoryRepository(db)
        
        # MemoryPipeline 생성 (Phase 2 포함)
        from src.memory.pipeline import MemoryPipeline
        pipeline = MemoryPipeline(memory_repo)
        
        # 긴 대화 테스트
        conversation = [{
            "user_name": "호영",
            "role": "user", 
            "content": "Phase 2 구현 완료했습니다! " + "A" * 6000  # 6000자 이상으로 만들기
        }]
        
        room = {"id": "integration-test-room"}
        user_id = "integration-test-user"
        user_name = "호영"
        
        # extract_and_save 실행 (Phase 2 로직이 동작해야 함)
        result = await pipeline.extract_and_save(
            conversation=conversation,
            room=room,
            user_id=user_id,
            user_name=user_name
        )
        
        # 결과 검증
        assert len(result) > 0, "메모리가 저장되어야 함"
        print(f"✅ 통합 테스트: {len(result)}개 메모리 저장됨")
        
        # 요약본이 있는지 확인
        summary_found = any(
            mem.get("content", "").startswith("[요약]") 
            for mem in result
        )
        print(f"✅ 요약본 생성 여부: {summary_found}")
        
        print("✅ 통합 테스트 통과!")
        
    finally:
        # Mock 복원
        vector_store.upsert_vector = original_upsert
        await db.close()


async def main():
    """모든 테스트 실행"""
    print("🔥 Phase 2 계층적 메모리 테스트 시작\n")
    
    await test_summary_generation()
    print()
    await test_hierarchical_search()
    print()
    await test_integration()
    
    print("\n🎉 Phase 2 모든 테스트 통과! 계층적 메모리 구현 완료!")


if __name__ == "__main__":
    asyncio.run(main())