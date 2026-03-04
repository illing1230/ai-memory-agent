"""
Phase 3: 적응형 청킹 시스템

내용 유형별 맞춤형 청킹 전략을 제공한다.
코드, 문서, 대화, 데이터 등 각 유형에 최적화된 분할 방식을 적용.
"""

import re
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.memory.chunking import IntelligentChunker, MessageChunk, ChunkMetadata


class ContentType(Enum):
    """내용 유형 분류"""
    CODE = "code"
    DOCUMENT = "document" 
    CONVERSATION = "conversation"
    DATA = "data"
    MIXED = "mixed"
    NATURAL = "natural"


@dataclass
class ContentAnalysis:
    """내용 분석 결과"""
    primary_type: ContentType
    confidence: float
    sections: Dict[str, Any]
    recommended_strategy: str
    complexity_score: float
    estimated_chunks: int


class SmartContentDetector:
    """지능형 내용 유형 감지기"""
    
    def __init__(self):
        # 코드 패턴들
        self.code_patterns = [
            r'\bdef\s+\w+\s*\(',        # Python 함수
            r'\bfunction\s+\w+\s*\(',   # JavaScript 함수
            r'\bclass\s+\w+\s*[:\(]',   # 클래스 정의
            r'\bimport\s+\w+',          # import 문
            r'\bfrom\s+\w+\s+import',   # from import
            r'```\w*\n',                # 코드 블록
            r'^\s*[a-zA-Z_]\w*\s*=',    # 변수 할당
            r'\bif\s+.*:\s*$',          # if 문
            r'\bfor\s+.*:\s*$',         # for 문
            r'\breturn\s+',             # return 문
        ]
        
        # 문서 패턴들
        self.document_patterns = [
            r'^#{1,6}\s+',              # 마크다운 헤더
            r'^\d+\.\s+',               # 번호 목록
            r'^\*\s+',                  # 불릿 포인트
            r'^\-\s+',                  # 불릿 포인트
            r'\*\*.*?\*\*',             # 볼드 텍스트
            r'__.*?__',                 # 언더라인
            r'\[.*?\]\(.*?\)',          # 마크다운 링크
        ]
        
        # 대화 패턴들
        self.conversation_patterns = [
            r'^\w+:\s+',                # 발화자: 내용
            r'^[가-힣]+:\s+',           # 한국어 이름:
            r'^\d{2}:\d{2}\s+',         # 시간 스탬프
            r'질문:\s+',                # Q&A 패턴
            r'답변:\s+',                # Q&A 패턴
        ]
        
        # 데이터 패턴들
        self.data_patterns = [
            r'\|.*?\|.*?\|',            # 테이블 행
            r'^\s*{.*}$',               # JSON 객체
            r'^\s*\[.*\]$',             # JSON 배열
            r':",\s*"',                 # JSON 키-값
            r'^\s*\w+\s*:\s*\w+',       # 키-값 쌍
            r'<\w+.*?</\w+>',           # XML/HTML 태그
        ]
    
    async def analyze(self, content: str) -> ContentAnalysis:
        """내용 분석 및 유형 감지"""
        lines = content.split('\n')
        
        # 각 패턴별 매칭 점수 계산
        code_score = self._calculate_pattern_score(content, self.code_patterns)
        doc_score = self._calculate_pattern_score(content, self.document_patterns)
        conv_score = self._calculate_pattern_score(content, self.conversation_patterns)
        data_score = self._calculate_pattern_score(content, self.data_patterns)
        
        # 추가 휴리스틱
        code_blocks = len(re.findall(r'```.*?```', content, re.DOTALL))
        table_rows = len(re.findall(r'\|.*?\|', content))
        speaker_changes = len(re.findall(r'^\w+:\s+', content, re.MULTILINE))
        
        # 점수 보정
        if code_blocks > 0:
            code_score += 0.3
        if table_rows > 3:
            data_score += 0.2
        if speaker_changes > 2:
            conv_score += 0.2
        
        # 최고 점수 유형 선택
        scores = {
            ContentType.CODE: code_score,
            ContentType.DOCUMENT: doc_score,
            ContentType.CONVERSATION: conv_score,
            ContentType.DATA: data_score
        }
        
        primary_type = max(scores, key=scores.get)
        confidence = scores[primary_type]
        
        # MIXED 유형 감지 (여러 유형이 높은 점수)
        high_scores = [k for k, v in scores.items() if v > 0.3]
        if len(high_scores) > 1:
            primary_type = ContentType.MIXED
            confidence = sum(scores.values()) / len(scores)
        
        # 모든 점수가 낮으면 NATURAL
        if confidence < 0.2:
            primary_type = ContentType.NATURAL
            confidence = 0.5
        
        # 복잡도 점수
        complexity_score = self._calculate_complexity(content, lines)
        
        # 예상 청크 수
        estimated_chunks = max(1, len(content) // 1500)
        
        # 섹션 분석
        sections = {
            "code_blocks": code_blocks,
            "table_rows": table_rows,
            "speaker_changes": speaker_changes,
            "line_count": len(lines),
            "avg_line_length": sum(len(line) for line in lines) / max(len(lines), 1)
        }
        
        # 추천 전략
        recommended_strategy = self._recommend_strategy(primary_type, sections)
        
        return ContentAnalysis(
            primary_type=primary_type,
            confidence=confidence,
            sections=sections,
            recommended_strategy=recommended_strategy,
            complexity_score=complexity_score,
            estimated_chunks=estimated_chunks
        )
    
    def _calculate_pattern_score(self, content: str, patterns: List[str]) -> float:
        """패턴 매칭 점수 계산"""
        matches = 0
        total_lines = len(content.split('\n'))
        
        for pattern in patterns:
            matches += len(re.findall(pattern, content, re.MULTILINE))
        
        return min(1.0, matches / max(total_lines * 0.1, 1))
    
    def _calculate_complexity(self, content: str, lines: List[str]) -> float:
        """내용 복잡도 계산"""
        factors = [
            len(content) / 10000,  # 길이
            len(lines) / 100,      # 라인 수
            len(re.findall(r'[{}[\]()]', content)) / 100,  # 구조 문자
            len(re.findall(r'\w+', content)) / 500  # 단어 수
        ]
        
        return min(1.0, sum(factors) / len(factors))
    
    def _recommend_strategy(self, content_type: ContentType, sections: Dict) -> str:
        """최적 청킹 전략 추천"""
        if content_type == ContentType.CODE:
            return "function_aware"
        elif content_type == ContentType.DOCUMENT:
            return "section_aware" 
        elif content_type == ContentType.CONVERSATION:
            return "speaker_aware"
        elif content_type == ContentType.DATA:
            return "structure_aware"
        elif content_type == ContentType.MIXED:
            return "hybrid"
        else:
            return "natural"


class CodeChunker:
    """코드 전용 청킹 전략"""
    
    def __init__(self, max_chunk_size: int = 2000):
        self.max_chunk_size = max_chunk_size
        
    async def chunk(self, content: str) -> List[MessageChunk]:
        """함수/클래스 단위로 코드 청킹"""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        indent_level = 0
        in_function = False
        
        for i, line in enumerate(lines):
            line_size = len(line) + 1
            
            # 함수/클래스 시작 감지
            if re.match(r'^(def |class |function |async def |public class )', line.strip()):
                # 이전 청크가 있고 크기가 적당하면 분할
                if current_chunk and current_size > 200:
                    chunk_content = '\n'.join(current_chunk)
                    chunks.append(self._create_code_chunk(chunk_content, len(chunks)))
                    current_chunk = []
                    current_size = 0
                
                in_function = True
                indent_level = len(line) - len(line.lstrip())
            
            # 함수 끝 감지 (들여쓰기 레벨 변화)
            elif in_function and line.strip() and len(line) - len(line.lstrip()) <= indent_level:
                if not line.startswith(' ' * (indent_level + 1)):
                    in_function = False
            
            current_chunk.append(line)
            current_size += line_size
            
            # 최대 크기 초과 시 강제 분할 (함수 중간이라도)
            if current_size >= self.max_chunk_size:
                chunk_content = '\n'.join(current_chunk)
                chunks.append(self._create_code_chunk(chunk_content, len(chunks)))
                current_chunk = []
                current_size = 0
                in_function = False
        
        # 마지막 청크
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunks.append(self._create_code_chunk(chunk_content, len(chunks)))
        
        # total_chunks 업데이트
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
            
        return chunks
    
    def _create_code_chunk(self, content: str, index: int) -> MessageChunk:
        """코드 청크 생성"""
        return MessageChunk(
            content=content,
            metadata=ChunkMetadata(
                chunk_index=index,
                total_chunks=1,  # 나중에 업데이트
                length=len(content),
                is_continuation=index > 0,
                overlap_start=0,
                overlap_end=0
            )
        )


class DocumentChunker:
    """문서 전용 청킹 전략"""
    
    def __init__(self, max_chunk_size: int = 1800):
        self.max_chunk_size = max_chunk_size
        
    async def chunk(self, content: str) -> List[MessageChunk]:
        """섹션/헤더 단위로 문서 청킹"""
        lines = content.split('\n')
        chunks = []
        current_section = []
        current_size = 0
        section_level = 0
        
        for line in lines:
            line_size = len(line) + 1
            
            # 마크다운 헤더 감지
            header_match = re.match(r'^(#{1,6})\s+(.+)', line)
            if header_match:
                header_level = len(header_match.group(1))
                
                # 같거나 상위 레벨 헤더면 섹션 분할
                if section_level > 0 and header_level <= section_level and current_section:
                    chunk_content = '\n'.join(current_section)
                    chunks.append(self._create_doc_chunk(chunk_content, len(chunks)))
                    current_section = []
                    current_size = 0
                
                section_level = header_level
            
            # 번호 목록이나 구분선도 섹션 구분자로 간주
            elif re.match(r'^([-=_*]{3,}|\d+\.\s+.+)$', line.strip()):
                if current_section and current_size > 300:
                    chunk_content = '\n'.join(current_section)
                    chunks.append(self._create_doc_chunk(chunk_content, len(chunks)))
                    current_section = []
                    current_size = 0
            
            current_section.append(line)
            current_size += line_size
            
            # 최대 크기 초과 시 강제 분할
            if current_size >= self.max_chunk_size:
                chunk_content = '\n'.join(current_section)
                chunks.append(self._create_doc_chunk(chunk_content, len(chunks)))
                current_section = []
                current_size = 0
                section_level = 0
        
        # 마지막 섹션
        if current_section:
            chunk_content = '\n'.join(current_section)
            chunks.append(self._create_doc_chunk(chunk_content, len(chunks)))
        
        # total_chunks 업데이트
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
            
        return chunks
    
    def _create_doc_chunk(self, content: str, index: int) -> MessageChunk:
        """문서 청크 생성"""
        return MessageChunk(
            content=content,
            metadata=ChunkMetadata(
                chunk_index=index,
                total_chunks=1,
                length=len(content),
                is_continuation=index > 0
            )
        )


class ConversationChunker:
    """대화 전용 청킹 전략"""
    
    def __init__(self, max_chunk_size: int = 1600):
        self.max_chunk_size = max_chunk_size
        
    async def chunk(self, content: str) -> List[MessageChunk]:
        """화자별/주제별로 대화 청킹"""
        lines = content.split('\n')
        chunks = []
        current_conversation = []
        current_size = 0
        current_speaker = None
        
        for line in lines:
            line_size = len(line) + 1
            
            # 화자 변경 감지
            speaker_match = re.match(r'^(\w+):\s+(.+)', line)
            if speaker_match:
                speaker = speaker_match.group(1)
                
                # 화자가 바뀌고 현재 청크가 충분히 큰 경우 분할
                if (current_speaker and speaker != current_speaker and 
                    current_size > 400 and len(current_conversation) > 3):
                    chunk_content = '\n'.join(current_conversation)
                    chunks.append(self._create_conv_chunk(chunk_content, len(chunks)))
                    current_conversation = []
                    current_size = 0
                
                current_speaker = speaker
            
            # 시간 스탬프나 주제 변경도 구분점으로 활용
            elif re.match(r'^\d{2}:\d{2}|\[.*\]|===|---', line.strip()):
                if current_conversation and current_size > 500:
                    chunk_content = '\n'.join(current_conversation)
                    chunks.append(self._create_conv_chunk(chunk_content, len(chunks)))
                    current_conversation = []
                    current_size = 0
                    current_speaker = None
            
            current_conversation.append(line)
            current_size += line_size
            
            # 최대 크기 초과 시 강제 분할
            if current_size >= self.max_chunk_size:
                chunk_content = '\n'.join(current_conversation)
                chunks.append(self._create_conv_chunk(chunk_content, len(chunks)))
                current_conversation = []
                current_size = 0
                current_speaker = None
        
        # 마지막 대화
        if current_conversation:
            chunk_content = '\n'.join(current_conversation)
            chunks.append(self._create_conv_chunk(chunk_content, len(chunks)))
        
        # total_chunks 업데이트
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
            
        return chunks
    
    def _create_conv_chunk(self, content: str, index: int) -> MessageChunk:
        """대화 청크 생성"""
        return MessageChunk(
            content=content,
            metadata=ChunkMetadata(
                chunk_index=index,
                total_chunks=1,
                length=len(content),
                is_continuation=index > 0
            )
        )


class DataChunker:
    """데이터 전용 청킹 전략"""
    
    def __init__(self, max_chunk_size: int = 1500):
        self.max_chunk_size = max_chunk_size
        
    async def chunk(self, content: str) -> List[MessageChunk]:
        """구조 보존 우선 데이터 청킹"""
        lines = content.split('\n')
        chunks = []
        current_structure = []
        current_size = 0
        in_table = False
        in_json = False
        json_level = 0
        
        for line in lines:
            line_size = len(line) + 1
            
            # 테이블 시작/끝 감지
            if '|' in line and line.count('|') >= 2:
                if not in_table:
                    in_table = True
                elif current_size > self.max_chunk_size:
                    # 테이블이 너무 크면 여기서 분할
                    chunk_content = '\n'.join(current_structure)
                    chunks.append(self._create_data_chunk(chunk_content, len(chunks)))
                    current_structure = []
                    current_size = 0
            elif in_table and '|' not in line:
                in_table = False
            
            # JSON 구조 감지
            if line.strip().startswith('{') or line.strip().startswith('['):
                in_json = True
                json_level = 0
            if in_json:
                json_level += line.count('{') + line.count('[')
                json_level -= line.count('}') + line.count(']')
                if json_level <= 0:
                    in_json = False
            
            # 구조가 완성된 시점에서 분할 판단
            can_split = not in_table and not in_json
            
            current_structure.append(line)
            current_size += line_size
            
            # 최대 크기 초과이고 분할 가능한 시점
            if current_size >= self.max_chunk_size and can_split and len(current_structure) > 5:
                chunk_content = '\n'.join(current_structure)
                chunks.append(self._create_data_chunk(chunk_content, len(chunks)))
                current_structure = []
                current_size = 0
        
        # 마지막 구조
        if current_structure:
            chunk_content = '\n'.join(current_structure)
            chunks.append(self._create_data_chunk(chunk_content, len(chunks)))
        
        # total_chunks 업데이트
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
            
        return chunks
    
    def _create_data_chunk(self, content: str, index: int) -> MessageChunk:
        """데이터 청크 생성"""
        return MessageChunk(
            content=content,
            metadata=ChunkMetadata(
                chunk_index=index,
                total_chunks=1,
                length=len(content),
                is_continuation=index > 0
            )
        )


class AdaptiveChunker:
    """적응형 청킹 마스터 클래스"""
    
    def __init__(self, 
                 max_chunk_size: int = 1500,
                 overlap_size: int = 150,
                 min_chunk_size: int = 200):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        
        # 내용 감지기
        self.detector = SmartContentDetector()
        
        # 전용 청킹 전략들
        self.chunkers = {
            "function_aware": CodeChunker(max_chunk_size),
            "section_aware": DocumentChunker(max_chunk_size),
            "speaker_aware": ConversationChunker(max_chunk_size),
            "structure_aware": DataChunker(max_chunk_size),
            "natural": IntelligentChunker(max_chunk_size, overlap_size, min_chunk_size)
        }
    
    async def chunk_message(self, content: str, preserve_structure: bool = True) -> List[MessageChunk]:
        """적응형 청킹 실행"""
        if len(content) <= self.max_chunk_size:
            return [self._create_single_chunk(content)]
        
        print(f"[적응형 청킹] 내용 분석 중... ({len(content)}자)")
        
        # 1. 내용 분석
        analysis = await self.detector.analyze(content)
        
        print(f"[적응형 청킹] 유형: {analysis.primary_type.value} (신뢰도: {analysis.confidence:.2f})")
        print(f"[적응형 청킹] 전략: {analysis.recommended_strategy}")
        
        # 2. 적합한 청킹 전략 선택
        if analysis.primary_type == ContentType.MIXED:
            chunks = await self._chunk_mixed_content(content, analysis)
        else:
            strategy = analysis.recommended_strategy
            if strategy in self.chunkers:
                chunker = self.chunkers[strategy]
                chunks = await chunker.chunk(content)
            else:
                # fallback to natural chunking
                chunks = await self.chunkers["natural"].chunk_message(content, preserve_structure)
        
        # 3. 오버랩 추가 (코드는 제외)
        if analysis.primary_type != ContentType.CODE:
            chunks = self._add_overlaps(chunks, content)
        
        print(f"[적응형 청킹] 완료: {len(chunks)}개 청크 생성")
        return chunks
    
    async def _chunk_mixed_content(self, content: str, analysis: ContentAnalysis) -> List[MessageChunk]:
        """혼합 내용 청킹 - 섹션별로 다른 전략 적용"""
        # 코드 블록과 일반 텍스트 분리
        code_blocks = list(re.finditer(r'```[\s\S]*?```', content))
        chunks = []
        last_end = 0
        
        for code_block in code_blocks:
            start, end = code_block.span()
            
            # 코드 블록 이전의 텍스트 (문서로 처리)
            if start > last_end:
                text_content = content[last_end:start].strip()
                if text_content:
                    doc_chunker = self.chunkers["section_aware"]
                    text_chunks = await doc_chunker.chunk(text_content)
                    chunks.extend(text_chunks)
            
            # 코드 블록 (코드로 처리)
            code_content = content[start:end].strip()
            if code_content:
                code_chunker = self.chunkers["function_aware"]
                code_chunks = await code_chunker.chunk(code_content)
                chunks.extend(code_chunks)
            
            last_end = end
        
        # 마지막 코드 블록 이후의 텍스트
        if last_end < len(content):
            remaining_content = content[last_end:].strip()
            if remaining_content:
                doc_chunker = self.chunkers["section_aware"]
                remaining_chunks = await doc_chunker.chunk(remaining_content)
                chunks.extend(remaining_chunks)
        
        # 청크 인덱스 재정렬
        for i, chunk in enumerate(chunks):
            chunk.metadata.chunk_index = i
            chunk.metadata.total_chunks = len(chunks)
        
        return chunks
    
    def _add_overlaps(self, chunks: List[MessageChunk], original_content: str) -> List[MessageChunk]:
        """청크 간 오버랩 추가 (코드 제외)"""
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
                content = f"...[이전 내용: {prev_overlap[:50]}...]\n\n{content}"
                chunk.metadata.overlap_start = len(prev_overlap) + 20
            
            # 다음 청크의 시작부분 오버랩 추가  
            if i < len(chunks) - 1:
                next_content = chunks[i+1].content
                next_overlap = next_content[:self.overlap_size]
                content = f"{content}\n\n[다음 내용: {next_overlap[:50]}...]"
                chunk.metadata.overlap_end = len(next_overlap) + 20
            
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
                )
            )
            
            overlapped_chunks.append(new_chunk)
        
        return overlapped_chunks
    
    def _create_single_chunk(self, content: str) -> MessageChunk:
        """단일 청크 생성"""
        return MessageChunk(
            content=content,
            metadata=ChunkMetadata(
                chunk_index=0,
                total_chunks=1,
                length=len(content),
                is_continuation=False
            )
        )


class BatchEmbeddingProcessor:
    """배치 임베딩 처리기 - Phase 3 성능 최적화"""
    
    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
        
    async def process_chunks(self, chunks: List[MessageChunk]) -> List[Tuple[MessageChunk, List[float]]]:
        """청크들을 배치로 임베딩 처리"""
        from src.shared.providers import get_embedding_provider
        
        embedding_provider = get_embedding_provider()
        results = []
        
        # 배치 단위로 처리
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_contents = [chunk.content for chunk in batch]
            
            try:
                # 배치 임베딩 (실제 구현에서는 provider가 배치를 지원해야 함)
                batch_vectors = []
                for content in batch_contents:
                    vector = await embedding_provider.embed(content)
                    batch_vectors.append(vector)
                
                # 결과 매칭
                for chunk, vector in zip(batch, batch_vectors):
                    results.append((chunk, vector))
                
                print(f"[배치 임베딩] {len(batch)}개 청크 처리 완료")
                
            except Exception as e:
                print(f"[배치 임베딩] 배치 처리 실패, 개별 처리로 fallback: {e}")
                # Fallback: 개별 처리
                for chunk in batch:
                    try:
                        vector = await embedding_provider.embed(chunk.content)
                        results.append((chunk, vector))
                    except Exception as individual_error:
                        print(f"[배치 임베딩] 개별 임베딩 실패: {individual_error}")
                        # 빈 벡터로 대체
                        results.append((chunk, [0.0] * 384))
        
        return results