"""
지능형 청킹 기능 테스트

새로운 chunking.py 모듈의 IntelligentChunker 클래스를 테스트한다.
"""

import asyncio
import sys
import os

# 테스트 환경 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory.chunking import IntelligentChunker, ContentTypeDetector


async def test_short_content():
    """짧은 내용 테스트 - 청킹하지 않음"""
    chunker = IntelligentChunker()
    content = "안녕하세요. 이것은 짧은 메시지입니다."
    
    chunks = await chunker.chunk_message(content)
    
    assert len(chunks) == 1
    assert chunks[0].content == content
    assert chunks[0].metadata.total_chunks == 1
    assert not chunks[0].metadata.is_continuation
    print("✅ 짧은 내용 테스트 통과")


async def test_long_natural_language():
    """긴 자연어 텍스트 청킹 테스트"""
    chunker = IntelligentChunker(max_chunk_size=500, overlap_size=50)
    
    # 긴 텍스트 생성
    content = """
안녕하세요. 저는 삼성전자에서 AI 기반 PLM 품질검사 업무를 담당하고 있는 호영입니다.

최근에 AI Memory Agent 프로젝트를 진행하고 있는데, 긴 메시지 처리에 문제가 있어서 개선작업을 하고 있습니다. 
기존에는 단순히 1500자로 자르는 방식이었는데, 이제 지능형 청킹으로 의미 단위로 분할하도록 개선했습니다.

이 프로젝트는 GitHub에서 관리하고 있고, feat/mchat-integration 브랜치에서 Mchat 통합을 개선하고 있었는데, 
이번에는 feat/intelligent-chunking 브랜치를 새로 만들어서 청킹 기능을 구현했습니다.

개선된 기능들은 다음과 같습니다:
1. 지능형 청킹 - 문단, 문장 단위로 의미있게 분할
2. 계층적 요약 - 요약본과 상세본 동시 저장  
3. 연결형 검색 - 요약 검색 후 연결된 청크 자동 확장
4. 적응형 청킹 - 코드, 문서, 대화별 맞춤 전략
5. 성능 최적화 - 배치 처리, 캐싱, 인덱싱

이렇게 개선하면 정보 손실 없이 긴 메시지도 완벽하게 처리할 수 있을 것 같습니다.
    """.strip()
    
    chunks = await chunker.chunk_message(content)
    
    print(f"청킹 결과: {len(chunks)}개 청크")
    for i, chunk in enumerate(chunks):
        print(f"청크 {i+1}: {len(chunk.content)}자, 연속여부: {chunk.metadata.is_continuation}")
        print(f"  내용: {chunk.content[:100]}...")
        print()
    
    # 검증
    assert len(chunks) > 1  # 여러 청크로 분할됨
    assert all(len(chunk.content) <= 550 for chunk in chunks)  # 각 청크는 최대 크기 준수 (오버랩 포함)
    assert chunks[0].metadata.chunk_index == 0
    assert chunks[-1].metadata.chunk_index == len(chunks) - 1
    
    print("✅ 긴 자연어 텍스트 청킹 테스트 통과")


async def test_code_content():
    """코드 내용 청킹 테스트"""
    chunker = IntelligentChunker(max_chunk_size=300)
    
    code_content = """
```python
def extract_and_save(self, conversation, room, user_id):
    # 긴 함수 예시
    result = []
    for msg in conversation:
        if len(msg) > 1000:
            # 긴 메시지 처리 로직
            chunks = self.chunk_message(msg)
            for chunk in chunks:
                extracted = self.extract_from_chunk(chunk)
                result.extend(extracted)
        else:
            # 짧은 메시지는 바로 처리
            extracted = self.extract_simple(msg)
            result.append(extracted)
    return result

class MemoryPipeline:
    def __init__(self):
        self.chunker = IntelligentChunker()
        
    async def process(self, data):
        # 또 다른 함수
        return await self.chunker.chunk_message(data)
```
    """.strip()
    
    chunks = await chunker.chunk_message(code_content)
    
    print(f"코드 청킹 결과: {len(chunks)}개 청크")
    for i, chunk in enumerate(chunks):
        print(f"청크 {i+1}: {len(chunk.content)}자")
        print(f"  내용: {chunk.content[:80].replace(chr(10), '\\n')}...")
        print()
    
    assert len(chunks) > 1
    print("✅ 코드 내용 청킹 테스트 통과")


async def test_content_type_detection():
    """내용 유형 감지 테스트"""
    detector = ContentTypeDetector()
    
    # 자연어
    natural = "안녕하세요. 오늘 날씨가 좋네요."
    result = detector.detect(natural)
    assert result["type"] == "natural"
    
    # 코드
    code = """
def hello():
    print("Hello World")
    return True
"""
    result = detector.detect(code)
    assert result["type"] == "code" or result["has_code"]
    
    # 구조화된 데이터
    structured = """
| 이름 | 나이 | 직업 |
|------|------|------|
| 홍길동 | 30 | 개발자 |
| 김철수 | 25 | 디자이너 |

- 항목 1
- 항목 2
- 항목 3
"""
    result = detector.detect(structured)
    assert result["type"] == "structured" or result["has_tables"] or result["has_lists"]
    
    print("✅ 내용 유형 감지 테스트 통과")


async def main():
    """모든 테스트 실행"""
    print("🔥 지능형 청킹 테스트 시작\n")
    
    await test_short_content()
    await test_long_natural_language()
    await test_code_content()
    await test_content_type_detection()
    
    print("\n🎉 모든 테스트 통과! 지능형 청킹 구현 완료!")


if __name__ == "__main__":
    asyncio.run(main())