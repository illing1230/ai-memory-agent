"""
계층적 메모리 관리 모듈

긴 메시지를 요약본 + 상세 청크로 분리 저장하고,
검색 시 요약본을 통해 연결된 청크들을 자동 확장한다.
"""

import uuid
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple

from src.memory.chunking import IntelligentChunker, MessageChunk
from src.memory.adaptive import AdaptiveChunker, BatchEmbeddingProcessor
from src.memory.repository import MemoryRepository
from src.memory.entity_repository import EntityRepository
from src.shared.vector_store import search_vectors, upsert_vector
from src.shared.providers import get_embedding_provider, get_llm_provider
from src.config import get_settings


class HierarchicalMemoryPipeline:
    """계층적 메모리 관리 파이프라인"""
    
    def __init__(
        self, 
        memory_repo: MemoryRepository,
        entity_repo: EntityRepository,
        chunker: IntelligentChunker | None = None,
        use_adaptive: bool = True
    ):
        self.memory_repo = memory_repo
        self.entity_repo = entity_repo
        self.settings = get_settings()
        
        # 🔥 Phase 3: 적응형 청킹 우선 사용
        if use_adaptive:
            self.chunker = AdaptiveChunker(
                max_chunk_size=1500,
                overlap_size=150,
                min_chunk_size=200
            )
            self.batch_processor = BatchEmbeddingProcessor(batch_size=5)
        else:
            self.chunker = chunker or IntelligentChunker()
            self.batch_processor = None
        
    async def extract_and_save_hierarchical(
        self,
        content: str,
        room: Dict[str, Any],
        user_id: str,
        user_name: str,
        memory_context: List[str] | None = None,
        threshold_length: int = 6000
    ) -> Tuple[Optional[Dict], List[Dict]]:
        """
        긴 메시지를 계층적으로 저장
        
        Returns:
            (summary_memory, chunk_memories): 요약 메모리와 청크 메모리들
        """
        print(f"[계층적 저장] 입력 길이: {len(content)}자")
        
        if len(content) <= threshold_length:
            print(f"[계층적 저장] 짧은 메시지, 일반 처리")
            return None, []
        
        try:
            # 1. 전체 요약 생성
            print(f"[계층적 저장] 요약 생성 중...")
            summary = await self._generate_comprehensive_summary(content, user_name)
            
            if not summary:
                print(f"[계층적 저장] 요약 생성 실패, 일반 청킹으로 fallback")
                return None, []
            
            # 2. 지능형 청킹으로 상세 분할
            print(f"[계층적 저장] 청킹 진행 중...")
            chunks = await self.chunker.chunk_message(content, preserve_structure=True)
            
            if len(chunks) <= 1:
                print(f"[계층적 저장] 청킹 불필요, 일반 처리")
                return None, []
            
            # 3. 요약본 저장 (상위 레벨)
            summary_memory = await self._save_summary_memory(
                summary=summary,
                original_content=content,
                user_id=user_id,
                room=room,
                total_chunks=len(chunks),
                user_name=user_name
            )
            
            if not summary_memory:
                print(f"[계층적 저장] 요약본 저장 실패")
                return None, []
            
            # 4. 청크들 저장 (하위 레벨) + 요약본과 연결
            chunk_memories = await self._save_linked_chunks(
                chunks=chunks,
                summary_id=summary_memory["id"],
                user_id=user_id,
                room=room,
                user_name=user_name,
                memory_context=memory_context
            )
            
            print(f"[계층적 저장] 완료 - 요약본 1개, 청크 {len(chunk_memories)}개")
            return summary_memory, chunk_memories
            
        except Exception as e:
            print(f"[계층적 저장] 처리 실패: {e}")
            return None, []
    
    async def _generate_comprehensive_summary(self, content: str, user_name: str) -> Optional[str]:
        """종합 요약 생성"""
        try:
            llm_provider = get_llm_provider()
            current_date = (datetime.now(timezone.utc) + timedelta(hours=9)).strftime("%Y년 %m월 %d일")
            
            system_prompt = f"""당신은 긴 대화/문서를 효과적으로 요약하는 전문가입니다.

주요 임무:
1. 핵심 정보를 놓치지 않고 간결하게 요약
2. 나중에 검색할 때 이 요약으로 전체 내용을 찾을 수 있도록 작성
3. 중요한 키워드와 개념을 포함

요약 규칙:
- 길이: 200-500자 (너무 짧지도, 길지도 않게)
- 핵심 주제와 결론을 명확히
- 고유명사, 날짜, 수치는 보존
- 발화자 이름({user_name}) 포함
- 검색 키워드가 될 만한 단어들 자연스럽게 포함

현재 날짜: {current_date}"""

            user_prompt = f"""다음 긴 대화/문서를 종합 요약해 주세요:

{content[:4000]}
{"... (이하 내용 계속)" if len(content) > 4000 else ""}

요약:"""

            summary = await llm_provider.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=800
            )
            
            summary = summary.strip()
            
            # 요약 품질 검증
            if len(summary) < 50:
                print(f"[요약] 너무 짧음: {len(summary)}자")
                return None
            if len(summary) > 1000:
                print(f"[요약] 너무 김, 자르기: {len(summary)}자")
                summary = summary[:1000] + "..."
            
            print(f"[요약] 생성 완료: {len(summary)}자")
            print(f"[요약] 내용: {summary[:100]}...")
            return summary
            
        except Exception as e:
            print(f"[요약] 생성 실패: {e}")
            return None
    
    async def _save_summary_memory(
        self,
        summary: str,
        original_content: str,
        user_id: str,
        room: Dict[str, Any],
        total_chunks: int,
        user_name: str
    ) -> Optional[Dict[str, Any]]:
        """요약본 메모리 저장"""
        try:
            embedding_provider = get_embedding_provider()
            
            # 요약본 content 구성
            summary_content = f"[요약] {summary}"
            
            # 메타데이터 구성
            metadata = {
                "type": "summary",
                "total_chunks": total_chunks,
                "original_length": len(original_content),
                "summary_length": len(summary),
                "created_by": "hierarchical_pipeline"
            }
            
            # 임베딩 생성 (요약 내용 기반)
            vector = await embedding_provider.embed(summary_content)
            vector_id = str(uuid.uuid4())
            
            # 메모리 저장
            memory = await self.memory_repo.create_memory(
                content=summary_content,
                owner_id=user_id,
                scope="chatroom",
                vector_id=vector_id,
                chat_room_id=room["id"],
                category="fact",
                importance="high",  # 요약본은 높은 중요도
                topic_key=f"summary_{datetime.now().isoformat()}",
                metadata=json.dumps(metadata)
            )
            
            # 벡터 저장
            payload = {
                "memory_id": memory["id"],
                "scope": "chatroom",
                "owner_id": user_id,
                "chat_room_id": room["id"],
                "type": "summary"
            }
            await upsert_vector(vector_id, vector, payload)
            
            print(f"[요약 저장] 성공: {memory['id'][:8]}...")
            return memory
            
        except Exception as e:
            print(f"[요약 저장] 실패: {e}")
            return None
    
    async def _save_linked_chunks(
        self,
        chunks: List[MessageChunk],
        summary_id: str,
        user_id: str,
        room: Dict[str, Any],
        user_name: str,
        memory_context: List[str] | None = None
    ) -> List[Dict[str, Any]]:
        """청크들을 요약본과 연결하여 저장"""
        chunk_memories = []
        
        for i, chunk in enumerate(chunks):
            try:
                # 청크별 메모리 추출
                chunk_extracted_memories = await self._extract_chunk_memories(
                    chunk=chunk,
                    summary_id=summary_id,
                    user_id=user_id,
                    room=room,
                    user_name=user_name,
                    memory_context=memory_context
                )
                
                chunk_memories.extend(chunk_extracted_memories)
                print(f"[청크 {i+1}/{len(chunks)}] {len(chunk_extracted_memories)}개 메모리 저장")
                
            except Exception as e:
                print(f"[청크 {i+1}] 저장 실패: {e}")
                continue
        
        return chunk_memories
    
    async def _extract_chunk_memories(
        self,
        chunk: MessageChunk,
        summary_id: str,
        user_id: str,
        room: Dict[str, Any],
        user_name: str,
        memory_context: List[str] | None = None
    ) -> List[Dict[str, Any]]:
        """단일 청크에서 메모리 추출 (요약본과 연결)"""
        import json as _json
        
        try:
            llm_provider = get_llm_provider()
            current_date = (datetime.now(timezone.utc) + timedelta(hours=9)).strftime("%Y년 %m월 %d일")
            
            # 청크 정보 포함 시스템 프롬프트
            chunk_info = f"\n[청크 정보: {chunk.metadata.chunk_index + 1}/{chunk.metadata.total_chunks}]"
            if chunk.metadata.is_continuation:
                chunk_info += "\n(이 텍스트는 긴 대화의 일부입니다.)"
            
            system_prompt = f"""대화에서 장기적으로 기억할 가치가 있는 정보를 추출하고 분류하세요.

현재 발화자: {user_name}{chunk_info}

중요 규칙:
- 사용자가 직접 말한 "사실/진술"만 추출
- 불완전하거나 애매한 정보는 추출하지 마세요
- 각각의 정보를 별도 메모리로 분리
- 추출할 메모리가 없으면 빈 배열 []

현재 날짜: {current_date}

응답 형식 (JSON 배열):
[
  {{
    "content": "추출된 메모리 내용",
    "category": "preference|fact|decision|relationship",
    "importance": "high|medium|low",
    "is_personal": true|false
  }}
]"""
            
            # 기존 컨텍스트 추가
            context_section = ""
            if memory_context:
                context_lines = "\n".join(f"- {m}" for m in memory_context[:3])
                context_section = f"\n\n[이미 저장된 메모리]:\n{context_lines}"
            
            llm_prompt = f"다음 대화 청크를 분석해주세요:{context_section}\n\n{chunk.content}"
            
            extracted_text = (await llm_provider.generate(
                prompt=llm_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=3000
            )).strip()
            
            # JSON 파싱
            cleaned = extracted_text
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()
            
            memory_items = _json.loads(cleaned)
            if not isinstance(memory_items, list):
                return []
            
            # 청크 메모리들 저장
            saved_memories = []
            for item in memory_items:
                if not isinstance(item, dict) or "content" not in item:
                    continue
                
                content = item["content"].strip()
                if len(content) < self.settings.min_message_length_for_extraction:
                    continue
                
                # 메타데이터에 요약본 연결 정보 추가
                metadata = {
                    "chunk_index": chunk.metadata.chunk_index,
                    "total_chunks": chunk.metadata.total_chunks,
                    "parent_summary_id": summary_id,
                    "is_chunk_memory": True
                }
                
                # 청크 정보를 포함한 content
                chunk_prefix = f"[{chunk.metadata.chunk_index + 1}/{chunk.metadata.total_chunks}] "
                content_with_info = chunk_prefix + content
                
                try:
                    memory = await self._save_chunk_memory(
                        content=content_with_info,
                        original_content=content,
                        user_id=user_id,
                        room=room,
                        metadata=metadata,
                        category=item.get("category", "fact"),
                        importance=item.get("importance", "medium")
                    )
                    
                    if memory:
                        saved_memories.append(memory)
                
                except Exception as save_error:
                    print(f"청크 메모리 저장 실패: {save_error}")
                    continue
            
            return saved_memories
            
        except _json.JSONDecodeError as e:
            print(f"청크 메모리 추출 JSON 파싱 실패: {e}")
            return []
        except Exception as e:
            print(f"청크 메모리 추출 실패: {e}")
            return []
    
    async def _save_chunk_memory(
        self,
        content: str,
        original_content: str,
        user_id: str,
        room: Dict[str, Any],
        metadata: Dict[str, Any],
        category: str = "fact",
        importance: str = "medium"
    ) -> Optional[Dict[str, Any]]:
        """단일 청크 메모리 저장"""
        try:
            embedding_provider = get_embedding_provider()
            
            # 중복 검사 (원본 content 기준)
            vector = await embedding_provider.embed(original_content)
            
            # 시맨틱 중복 검사
            filter_conditions = {
                "owner_id": user_id,
                "chat_room_id": room["id"]
            }
            
            duplicates = await search_vectors(
                query_vector=vector,
                limit=3,
                score_threshold=0.93,
                filter_conditions=filter_conditions
            )
            
            # 중복 검사
            for dup in duplicates:
                existing_memory = await self.memory_repo.get_memory(dup["payload"].get("memory_id"))
                if existing_memory and not existing_memory.get("superseded", False):
                    content_words = set(original_content.split())
                    existing_words = set(existing_memory["content"].split())
                    word_similarity = len(content_words & existing_words) / max(len(content_words), len(existing_words), 1)
                    if dup["score"] >= 0.95 and word_similarity > 0.85:
                        print(f"중복 메모리 감지, 저장 스킵")
                        return None
            
            # 새 메모리 저장
            vector_id = str(uuid.uuid4())
            
            memory = await self.memory_repo.create_memory(
                content=content,
                owner_id=user_id,
                scope="chatroom",
                vector_id=vector_id,
                chat_room_id=room["id"],
                category=category,
                importance=importance,
                metadata=json.dumps(metadata)
            )
            
            # 벡터 저장
            payload = {
                "memory_id": memory["id"],
                "scope": "chatroom",
                "owner_id": user_id,
                "chat_room_id": room["id"],
                "parent_summary_id": metadata.get("parent_summary_id"),
                "type": "chunk"
            }
            await upsert_vector(vector_id, vector, payload)
            
            return memory
            
        except Exception as e:
            print(f"청크 메모리 저장 실패: {e}")
            return None


class HierarchicalSearchPipeline:
    """계층적 검색 파이프라인"""
    
    def __init__(self, memory_repo: MemoryRepository):
        self.memory_repo = memory_repo
    
    async def search_with_expansion(
        self,
        query: str,
        user_id: str,
        current_room_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """요약본 검색 → 연결된 청크 확장 검색"""
        print(f"\n========== 계층적 검색 시작 ==========")
        
        # 1. 일반 검색 (요약본 + 일반 메모리)
        embedding_provider = get_embedding_provider()
        query_vector = await embedding_provider.embed(query)
        
        # 벡터 검색
        search_results = await search_vectors(
            query_vector=query_vector,
            limit=limit,
            filter_conditions={
                "chat_room_id": current_room_id,
                "owner_id": user_id
            }
        )
        
        print(f"[계층적 검색] 기본 검색 결과: {len(search_results)}개")
        
        # 2. 메모리 메타데이터 배치 조회
        memory_ids = [r["payload"].get("memory_id") for r in search_results if r["payload"].get("memory_id")]
        
        if not memory_ids:
            print("========== 검색 결과 없음 ==========\n")
            return []
        
        memories = await self.memory_repo.get_memories_by_ids(memory_ids)
        memories_by_id = {m["id"]: m for m in memories}
        
        # 3. 요약본 감지 및 연결된 청크 확장
        expanded_results = []
        processed_summary_ids = set()
        
        for search_result in search_results:
            memory_id = search_result["payload"].get("memory_id")
            if not memory_id:
                continue
                
            memory = memories_by_id.get(memory_id)
            if not memory:
                continue
            
            # 요약본인지 확인
            if memory["content"].startswith("[요약]"):
                print(f"[계층적 검색] 요약본 발견: {memory['id'][:8]}...")
                
                if memory["id"] not in processed_summary_ids:
                    # 요약본 추가
                    expanded_results.append({
                        "memory": memory,
                        "score": search_result["score"],
                        "type": "summary"
                    })
                    
                    # 연결된 청크들 조회
                    linked_chunks = await self._get_linked_chunks(memory["id"])
                    for chunk in linked_chunks:
                        expanded_results.append({
                            "memory": chunk,
                            "score": search_result["score"] * 0.9,  # 요약본보다 약간 낮은 점수
                            "type": "chunk",
                            "parent_summary_id": memory["id"]
                        })
                    
                    processed_summary_ids.add(memory["id"])
                    print(f"[계층적 검색] 연결된 청크 {len(linked_chunks)}개 확장")
            else:
                # 일반 메모리 또는 독립 청크
                expanded_results.append({
                    "memory": memory,
                    "score": search_result["score"],
                    "type": "normal"
                })
        
        # 4. 점수 기준 정렬 및 제한
        expanded_results.sort(key=lambda x: x["score"], reverse=True)
        result = expanded_results[:limit]
        
        print(f"========== 계층적 검색 완료: {len(result)}개 ==========")
        for r in result[:5]:  # 상위 5개만 출력
            mem_type = r.get("type", "unknown")
            content_preview = r["memory"]["content"][:50] + "..."
            print(f"  [{mem_type}] {content_preview} (score: {r['score']:.3f})")
        print("")
        
        return result
    
    async def _get_linked_chunks(self, summary_id: str) -> List[Dict[str, Any]]:
        """요약본에 연결된 모든 청크 조회"""
        try:
            cursor = await self.memory_repo.db.execute("""
                SELECT * FROM memories 
                WHERE JSON_EXTRACT(metadata, '$.parent_summary_id') = ?
                ORDER BY JSON_EXTRACT(metadata, '$.chunk_index')
            """, (summary_id,))
            
            rows = await cursor.fetchall()
            chunks = []
            
            for row in rows:
                chunk = dict(row)
                if chunk.get("metadata"):
                    try:
                        chunk["metadata"] = json.loads(chunk["metadata"])
                    except:
                        chunk["metadata"] = {}
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"연결된 청크 조회 실패: {e}")
            return []