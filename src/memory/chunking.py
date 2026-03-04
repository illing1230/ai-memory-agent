"""
지능형 청킹 모듈 - 긴 메시지를 의미 단위로 분할

단순 문자 수 제한 대신 문단, 문장 단위로 의미있게 분할하고
오버랩을 통해 컨텍스트 연결성을 유지한다.
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ChunkMetadata:
    """청크 메타데이터"""
    chunk_index: int
    total_chunks: int
    length: int
    is_continuation: bool
    overlap_start: int = 0
    overlap_end: int = 0


@dataclass
class MessageChunk:
    """메시지 청크"""
    content: str
    metadata: ChunkMetadata
    original_start: int = 0
    original_end: int = 0


class IntelligentChunker:
    """지능형 청킹 엔진"""
    
    def __init__(
        self, 
        max_chunk_size: int = 1500, 
        overlap_size: int = 150,
        min_chunk_size: int = 200
    ):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        
    async def chunk_message(self, content: str, preserve_structure: bool = True) -> List[MessageChunk]:
        """메시지를 지능적으로 청킹"""
        if len(content) <= self.max_chunk_size:
            return [self._create_single_chunk(content)]
            
        content_type = self._detect_content_type(content)
        
        if content_type == "code":
            return await self._chunk_code_content(content)
        elif content_type == "structured":
            return await self._chunk_structured_content(content)
        else:
            return await self._chunk_natural_language(content, preserve_structure)
    
    def _detect_content_type(self, content: str) -> str:
        """내용 유형 감지"""
        # 코드 블록 감지
        if "```" in content or content.count('\n') > 10 and any(
            keyword in content for keyword in ['def ', 'function', 'class ', 'import ', 'const ', 'let ', 'var ']
        ):
            return "code"
            
        # 구조화된 데이터 감지 (표, JSON, 목록 등)
        if content.count('|') > 3 or content.count('\n-') > 3 or content.count('\n*') > 3:
            return "structured"
            
        return "natural"
    
    async def _chunk_natural_language(self, content: str, preserve_structure: bool) -> List[MessageChunk]:
        """자연어 텍스트 청킹"""
        chunks = []
        
        if preserve_structure:
            # 문단 단위 분할 시도
            paragraphs = self._split_paragraphs(content)
            chunks = await self._chunk_by_paragraphs(paragraphs, content)
        
        if not chunks:
            # 문단 분할 실패 시 문장 단위 분할
            sentences = self._split_sentences(content)
            chunks = await self._chunk_by_sentences(sentences, content)
        
        return self._add_overlaps(chunks, content)
    
    async def _chunk_code_content(self, content: str) -> List[MessageChunk]:
        """코드 내용 청킹 - 함수/클래스 단위 우선"""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        indent_level = 0
        
        for i, line in enumerate(lines):
            line_size = len(line) + 1  # +1 for newline
            
            # 함수/클래스 시작점 감지
            if re.match(r'^(def |class |function |async def )', line.strip()):
                # 이전 청크가 있고 크기가 적당하면 분할
                if current_chunk and current_size > self.min_chunk_size:
                    chunk_content = '\n'.join(current_chunk)
                    chunks.append(self._create_chunk(chunk_content, len(chunks)))
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(line)
            current_size += line_size
            
            # 최대 크기 초과 시 강제 분할
            if current_size >= self.max_chunk_size:
                chunk_content = '\n'.join(current_chunk)
                chunks.append(self._create_chunk(chunk_content, len(chunks)))
                current_chunk = []
                current_size = 0
        
        # 마지막 청크
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunks.append(self._create_chunk(chunk_content, len(chunks)))
        
        # total_chunks 업데이트
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
            
        return chunks
    
    async def _chunk_structured_content(self, content: str) -> List[MessageChunk]:
        """구조화된 데이터 청킹 - 논리적 섹션 단위"""
        lines = content.split('\n')
        chunks = []
        current_section = []
        current_size = 0
        
        for line in lines:
            line_size = len(line) + 1
            
            # 섹션 구분자 감지 (헤더, 구분선 등)
            if self._is_section_delimiter(line):
                if current_section and current_size > self.min_chunk_size:
                    chunk_content = '\n'.join(current_section)
                    chunks.append(self._create_chunk(chunk_content, len(chunks)))
                    current_section = []
                    current_size = 0
            
            current_section.append(line)
            current_size += line_size
            
            if current_size >= self.max_chunk_size:
                chunk_content = '\n'.join(current_section)
                chunks.append(self._create_chunk(chunk_content, len(chunks)))
                current_section = []
                current_size = 0
        
        if current_section:
            chunk_content = '\n'.join(current_section)
            chunks.append(self._create_chunk(chunk_content, len(chunks)))
        
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
            
        return chunks
    
    def _is_section_delimiter(self, line: str) -> bool:
        """섹션 구분자 판별"""
        stripped = line.strip()
        
        # 마크다운 헤더
        if stripped.startswith('#'):
            return True
            
        # 구분선
        if re.match(r'^[-=_*]{3,}$', stripped):
            return True
            
        # 번호 목록
        if re.match(r'^\d+\.\s', stripped):
            return True
            
        return False
    
    def _split_paragraphs(self, content: str) -> List[str]:
        """문단 단위 분할"""
        # 연속된 줄바꿈을 문단 구분자로 사용
        paragraphs = re.split(r'\n\s*\n', content)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_sentences(self, content: str) -> List[str]:
        """문장 단위 분할"""
        # 한국어 + 영어 문장 구분자
        sentences = re.split(r'[.!?]+\s+|[。！？]+\s*', content)
        return [s.strip() for s in sentences if s.strip()]
    
    async def _chunk_by_paragraphs(self, paragraphs: List[str], original_content: str) -> List[MessageChunk]:
        """문단 단위 청킹"""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para) + 2  # +2 for paragraph separator
            
            # 단일 문단이 너무 큰 경우 문장 단위로 재분할
            if para_size > self.max_chunk_size:
                if current_chunk:
                    chunk_content = '\n\n'.join(current_chunk)
                    chunks.append(self._create_chunk(chunk_content, len(chunks)))
                    current_chunk = []
                    current_size = 0
                
                # 큰 문단을 문장 단위로 분할
                sentences = self._split_sentences(para)
                sentence_chunks = await self._chunk_by_sentences(sentences, para)
                chunks.extend(sentence_chunks)
                continue
            
            # 현재 청크에 추가하면 크기 초과하는 경우
            if current_size + para_size > self.max_chunk_size and current_chunk:
                chunk_content = '\n\n'.join(current_chunk)
                chunks.append(self._create_chunk(chunk_content, len(chunks)))
                current_chunk = []
                current_size = 0
            
            current_chunk.append(para)
            current_size += para_size
        
        # 마지막 청크
        if current_chunk:
            chunk_content = '\n\n'.join(current_chunk)
            chunks.append(self._create_chunk(chunk_content, len(chunks)))
        
        return chunks
    
    async def _chunk_by_sentences(self, sentences: List[str], original_content: str) -> List[MessageChunk]:
        """문장 단위 청킹"""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence) + 1
            
            # 단일 문장이 너무 큰 경우 강제 분할
            if sentence_size > self.max_chunk_size:
                if current_chunk:
                    chunk_content = ' '.join(current_chunk)
                    chunks.append(self._create_chunk(chunk_content, len(chunks)))
                    current_chunk = []
                    current_size = 0
                
                # 긴 문장을 강제로 분할
                while len(sentence) > self.max_chunk_size:
                    split_point = self.max_chunk_size - 20  # 여유공간
                    chunk_part = sentence[:split_point] + "..."
                    chunks.append(self._create_chunk(chunk_part, len(chunks)))
                    sentence = "..." + sentence[split_point:]
                
                if sentence:
                    chunks.append(self._create_chunk(sentence, len(chunks)))
                continue
            
            if current_size + sentence_size > self.max_chunk_size and current_chunk:
                chunk_content = ' '.join(current_chunk)
                chunks.append(self._create_chunk(chunk_content, len(chunks)))
                current_chunk = []
                current_size = 0
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        if current_chunk:
            chunk_content = ' '.join(current_chunk)
            chunks.append(self._create_chunk(chunk_content, len(chunks)))
        
        return chunks
    
    def _add_overlaps(self, chunks: List[MessageChunk], original_content: str) -> List[MessageChunk]:
        """청크 간 오버랩 추가"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            content = chunk.content
            
            # 이전 청크의 끝부분 오버랩 추가
            if i > 0:
                prev_content = chunks[i-1].content
                overlap_start = max(0, len(prev_content) - self.overlap_size)
                prev_overlap = prev_content[overlap_start:]
                content = f"...{prev_overlap}\n\n{content}"
                chunk.metadata.overlap_start = len(prev_overlap) + 5  # "...\n\n" 길이 포함
            
            # 다음 청크의 시작부분 오버랩 추가
            if i < len(chunks) - 1:
                next_content = chunks[i+1].content
                next_overlap = next_content[:self.overlap_size]
                content = f"{content}\n\n{next_overlap}..."
                chunk.metadata.overlap_end = len(next_overlap) + 5
            
            # 새로운 청크 생성
            new_chunk = MessageChunk(
                content=content,
                metadata=ChunkMetadata(
                    chunk_index=chunk.metadata.chunk_index,
                    total_chunks=chunk.metadata.total_chunks,
                    length=len(content),
                    is_continuation=chunk.metadata.is_continuation,
                    overlap_start=chunk.metadata.overlap_start,
                    overlap_end=chunk.metadata.overlap_end
                ),
                original_start=chunk.original_start,
                original_end=chunk.original_end
            )
            
            overlapped_chunks.append(new_chunk)
        
        return overlapped_chunks
    
    def _create_chunk(self, content: str, chunk_index: int) -> MessageChunk:
        """단일 청크 생성"""
        return MessageChunk(
            content=content,
            metadata=ChunkMetadata(
                chunk_index=chunk_index,
                total_chunks=1,  # 나중에 업데이트
                length=len(content),
                is_continuation=chunk_index > 0
            )
        )
    
    def _create_single_chunk(self, content: str) -> MessageChunk:
        """단일 청크 생성 (분할 불필요)"""
        return MessageChunk(
            content=content,
            metadata=ChunkMetadata(
                chunk_index=0,
                total_chunks=1,
                length=len(content),
                is_continuation=False
            )
        )


class ContentTypeDetector:
    """내용 유형 감지기"""
    
    @staticmethod
    def detect(content: str) -> Dict[str, Any]:
        """내용 유형과 특성 감지"""
        result = {
            "type": "natural",
            "has_code": False,
            "has_tables": False,
            "has_lists": False,
            "structure_complexity": "low",
            "estimated_chunks": 1
        }
        
        lines = content.split('\n')
        
        # 코드 감지
        if "```" in content or any(
            keyword in content for keyword in 
            ['def ', 'function', 'class ', 'import ', 'const ', 'let ', 'var ', 'public class']
        ):
            result["has_code"] = True
            result["type"] = "code"
        
        # 표 감지
        if content.count('|') > 3:
            result["has_tables"] = True
            result["type"] = "structured"
        
        # 목록 감지
        list_markers = ['\n- ', '\n* ', '\n+ ']
        if any(marker in content for marker in list_markers) or content.count('\n1. ') > 1:
            result["has_lists"] = True
            if result["type"] == "natural":
                result["type"] = "structured"
        
        # 복잡도 추정
        if len(lines) > 50 or len(content) > 5000:
            result["structure_complexity"] = "high"
        elif len(lines) > 20 or len(content) > 2000:
            result["structure_complexity"] = "medium"
        
        # 예상 청크 수
        result["estimated_chunks"] = max(1, len(content) // 1500)
        
        return result