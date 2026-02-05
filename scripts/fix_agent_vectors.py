#!/usr/bin/env python3
"""Agent 메모리 벡터 재생성 스크립트

기존 Agent 메모리들의 벡터에 agent_instance_id를 추가하여 검색이 가능하도록 수정
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.shared.database import get_db, init_database
from src.shared.vector_store import upsert_vector, delete_vector
from src.shared.providers import get_embedding_provider


async def fix_agent_vectors():
    """Agent 메모리 벡터 재생성"""
    # 데이터베이스 초기화
    await init_database()
    
    async for db in get_db():
        # Agent 메모리 조회
        cursor = await db.execute("""
            SELECT id, content, owner_id, vector_id, metadata
            FROM memories
            WHERE scope = 'agent' AND vector_id IS NOT NULL
        """)
        rows = await cursor.fetchall()
        
        print(f"총 {len(rows)}개의 Agent 메모리를 찾았습니다.")
        
        embedding_provider = get_embedding_provider()
        fixed_count = 0
        error_count = 0
        
        for row in rows:
            memory_id = row["id"]
            content = row["content"]
            owner_id = row["owner_id"]
            vector_id = row["vector_id"]
            metadata = row["metadata"]
            
            # metadata에서 agent_instance_id 추출
            agent_instance_id = None
            if metadata:
                try:
                    import json
                    if isinstance(metadata, str):
                        metadata = json.loads(metadata)
                    agent_instance_id = metadata.get("agent_instance_id")
                except Exception as e:
                    print(f"  [오류] 메모리 {memory_id}의 metadata 파싱 실패: {e}")
                    error_count += 1
                    continue
            
            if not agent_instance_id:
                print(f"  [건너뜀] 메모리 {memory_id}: agent_instance_id가 없음")
                continue
            
            try:
                # 벡터 재생성
                vector = await embedding_provider.embed(content)
                
                # 기존 벡터 삭제
                await delete_vector(vector_id)
                
                # 새로운 벡터 저장 (agent_instance_id 포함)
                await upsert_vector(
                    vector_id=vector_id,
                    vector=vector,
                    payload={
                        "memory_id": memory_id,
                        "scope": "agent",
                        "owner_id": owner_id,
                        "agent_instance_id": agent_instance_id,
                    },
                )
                
                print(f"  [수정] 메모리 {memory_id}: agent_instance_id={agent_instance_id}")
                fixed_count += 1
                
            except Exception as e:
                print(f"  [오류] 메모리 {memory_id} 처리 실패: {e}")
                error_count += 1
        
        print(f"\n완료!")
        print(f"  수정됨: {fixed_count}개")
        print(f"  오류: {error_count}개")
        break


if __name__ == "__main__":
    asyncio.run(fix_agent_vectors())
