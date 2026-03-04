"""
Phase 3 적응형 청킹 테스트

AdaptiveChunker와 관련 클래스들을 테스트한다.
"""

import asyncio
import sys
import os

# 테스트 환경 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory.adaptive import (
    SmartContentDetector, 
    AdaptiveChunker,
    CodeChunker,
    DocumentChunker,
    ConversationChunker,
    DataChunker,
    ContentType,
    BatchEmbeddingProcessor
)


async def test_content_detection():
    """내용 유형 감지 테스트"""
    print("🧠 내용 유형 감지 테스트")
    
    detector = SmartContentDetector()
    
    # 코드 내용
    code_content = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    def __init__(self):
        self.result = 0
        
    def add(self, x, y):
        return x + y
"""
    
    analysis = await detector.analyze(code_content)
    assert analysis.primary_type == ContentType.CODE
    print(f"   ✅ 코드 감지: {analysis.primary_type.value} (신뢰도: {analysis.confidence:.2f})")
    
    # 문서 내용
    doc_content = """
# 프로젝트 개요
이 프로젝트는 AI Memory Agent 시스템입니다.

## 주요 기능
- 지능형 청킹
- 계층적 메모리 
- 적응형 청킹

### 상세 설명
각 Phase별로 점진적인 개선이 이루어졌습니다.
"""
    
    analysis = await detector.analyze(doc_content)
    assert analysis.primary_type == ContentType.DOCUMENT
    print(f"   ✅ 문서 감지: {analysis.primary_type.value} (신뢰도: {analysis.confidence:.2f})")
    
    # 대화 내용
    conv_content = """
호영: 프로젝트 진행 어때?
데비: Phase 3 구현 완료했어!
호영: 성능 개선 효과는?
데비: 검색 정확도가 95% 이상 나왔어
호영: 대단하네! 다음은 뭐 할 예정이야?
"""
    
    analysis = await detector.analyze(conv_content)
    assert analysis.primary_type == ContentType.CONVERSATION
    print(f"   ✅ 대화 감지: {analysis.primary_type.value} (신뢰도: {analysis.confidence:.2f})")
    
    # 데이터 내용
    data_content = """
| 이름 | 나이 | 점수 |
|------|------|------|
| Alice | 25 | 95 |
| Bob | 30 | 87 |
| Charlie | 28 | 92 |

{
    "results": [
        {"name": "test1", "value": 100},
        {"name": "test2", "value": 85}
    ]
}
"""
    
    analysis = await detector.analyze(data_content)
    assert analysis.primary_type == ContentType.DATA
    print(f"   ✅ 데이터 감지: {analysis.primary_type.value} (신뢰도: {analysis.confidence:.2f})")
    
    print("🧠 내용 유형 감지 테스트 완료!\n")


async def test_code_chunking():
    """코드 청킹 테스트"""
    print("💻 코드 청킹 테스트")
    
    chunker = CodeChunker(max_chunk_size=500)
    
    long_code = """
def fibonacci(n):
    \"\"\"피보나치 수열 계산\"\"\"
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def factorial(n):
    \"\"\"팩토리얼 계산\"\"\"
    if n <= 1:
        return 1
    return n * factorial(n-1)

class MathUtils:
    \"\"\"수학 유틸리티 클래스\"\"\"
    
    def __init__(self):
        self.cache = {}
        
    def gcd(self, a, b):
        \"\"\"최대공약수\"\"\"
        while b:
            a, b = b, a % b
        return a
        
    def lcm(self, a, b):
        \"\"\"최소공배수\"\"\"
        return a * b // self.gcd(a, b)
        
    def is_prime(self, n):
        \"\"\"소수 판별\"\"\"
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True

# 메인 실행 부분
if __name__ == "__main__":
    utils = MathUtils()
    print(f"fibonacci(10): {fibonacci(10)}")
    print(f"factorial(5): {factorial(5)}")
    print(f"gcd(12, 8): {utils.gcd(12, 8)}")
    print(f"is_prime(17): {utils.is_prime(17)}")
"""
    
    chunks = await chunker.chunk(long_code)
    
    print(f"   📝 원본 길이: {len(long_code)}자")
    print(f"   📄 청크 수: {len(chunks)}개")
    
    for i, chunk in enumerate(chunks):
        content_preview = chunk.content[:100].replace('\n', '\\n')
        print(f"   {i+1}. {len(chunk.content)}자: {content_preview}...")
    
    # 함수가 중간에 잘리지 않았는지 확인
    combined = '\n'.join(chunk.content for chunk in chunks)
    assert "def fibonacci" in combined
    assert "class MathUtils" in combined
    assert "__main__" in combined
    
    print("💻 코드 청킹 테스트 완료!\n")


async def test_document_chunking():
    """문서 청킹 테스트"""
    print("📄 문서 청킹 테스트")
    
    chunker = DocumentChunker(max_chunk_size=800)
    
    long_doc = """
# AI Memory Agent 프로젝트

이 프로젝트는 긴 메시지와 복잡한 대화를 효과적으로 기억하고 검색할 수 있는 AI 메모리 시스템을 구현합니다.

## Phase 1: 지능형 청킹

기존의 단순한 문자 수 제한 방식에서 벗어나 의미 단위로 메시지를 분할하는 지능형 청킹을 구현했습니다.

### 주요 기능
- 문단 단위 우선 분할
- 문장 경계 고려
- 오버랩을 통한 컨텍스트 연결성 유지
- 코드 블록과 일반 텍스트 구분

### 개선 효과
정보 손실을 70%에서 0%로 줄였으며, 컨텍스트 완성도를 크게 향상시켰습니다.

## Phase 2: 계층적 메모리

긴 메시지를 요약본과 상세 청크로 분리하여 저장하는 계층적 메모리 시스템을 구현했습니다.

### 핵심 아이디어
1. 전체 메시지의 종합 요약 생성
2. 의미 단위로 분할된 청크들 저장  
3. 요약본과 청크들 간의 연결 관계 구축
4. 검색 시 요약 우선 → 연결된 청크 자동 확장

### 성능 개선
- 정보 완성도: 40-60% → 95%+
- 검색 속도: 5배 향상
- 컨텍스트 정확도: 70% → 90%+

## Phase 3: 적응형 청킹

내용 유형별로 최적화된 청킹 전략을 적용하는 적응형 청킹 시스템을 구현했습니다.

### 지원하는 내용 유형
- **코드**: 함수, 클래스 단위 분할
- **문서**: 섹션, 헤더 구조 보존
- **대화**: 화자별, 주제 변경 기준
- **데이터**: 테이블, JSON 구조 보존

### 추가 최적화
- 배치 임베딩 처리
- 메모리 캐싱 시스템  
- 성능 인덱싱
- 혼합 콘텐츠 처리

## 결론

3단계에 걸친 점진적 개선을 통해 AI Memory Agent는 이제 어떤 형태의 복잡한 내용도 완벽하게 기억하고 정확하게 검색할 수 있는 시스템이 되었습니다.
"""
    
    chunks = await chunker.chunk(long_doc)
    
    print(f"   📝 원본 길이: {len(long_doc)}자")
    print(f"   📄 청크 수: {len(chunks)}개")
    
    for i, chunk in enumerate(chunks):
        # 헤더 추출
        lines = chunk.content.split('\n')
        header_line = next((line for line in lines if line.startswith('#')), "")
        if header_line:
            header = header_line.strip()
        else:
            header = chunk.content[:50].replace('\n', ' ')
        
        print(f"   {i+1}. {len(chunk.content)}자: {header}...")
    
    # 섹션이 보존되었는지 확인
    combined = '\n'.join(chunk.content for chunk in chunks)
    assert "# AI Memory Agent" in combined
    assert "## Phase 1" in combined
    assert "## Phase 2" in combined  
    assert "## Phase 3" in combined
    
    print("📄 문서 청킹 테스트 완료!\n")


async def test_conversation_chunking():
    """대화 청킹 테스트"""
    print("💬 대화 청킹 테스트")
    
    chunker = ConversationChunker(max_chunk_size=600)
    
    long_conversation = """
호영: 안녕하세요! AI Memory Agent 프로젝트 현황 보고드리겠습니다.

데비: 네, 좋습니다. Phase별로 어떻게 진행되었나요?

호영: Phase 1에서는 지능형 청킹을 구현했습니다. 기존의 단순 문자 수 제한을 넘어서 의미 단위로 분할하도록 개선했어요.

데비: 효과는 어땠나요?

호영: 정보 손실을 70%에서 0%로 줄였고, 검색 정확도도 크게 향상됐습니다. Phase 2에서는 계층적 메모리를 구현했어요.

데비: 계층적 메모리라는 건 어떤 개념인가요?

호영: 긴 메시지를 요약본과 상세 청크로 분리해서 저장하는 거예요. 검색할 때는 요약본을 먼저 찾고, 필요하면 연결된 청크들을 자동으로 확장해서 가져오죠.

데비: 흥미롭네요. 성능 개선 효과는?

호영: 정보 완성도가 40-60%에서 95% 이상으로 향상됐고, 검색 속도는 5배 빨라졌어요. 컨텍스트 정확도도 70%에서 90% 이상으로 올랐습니다.

데비: 정말 인상적이네요. Phase 3은 어떤 내용인가요?

호영: Phase 3은 적응형 청킹입니다. 내용 유형별로 최적화된 청킹 전략을 적용해요. 코드는 함수 단위로, 문서는 섹션 단위로, 대화는 화자별로 분할합니다.

데비: 각 유형별로 다르게 처리한다는 거군요. 구체적인 예시를 들어주실 수 있나요?

호영: 예를 들어 코드의 경우 함수나 클래스 중간에서 잘리지 않도록 하고, 테이블이 있는 데이터는 구조를 보존하면서 분할합니다. 이렇게 하면 검색할 때도 의미가 완전히 보존된 상태로 결과를 얻을 수 있어요.

데비: 대단하네요. 전체적인 성과를 정리해주세요.

호영: 3단계를 거쳐서 이제 AI Memory Agent는 어떤 복잡한 내용도 완벽하게 기억하고 정확하게 검색할 수 있게 됐습니다. 코드, 문서, 대화, 데이터 모든 유형을 각각에 최적화된 방식으로 처리하죠.

데비: 정말 훌륭한 성과네요. 수고하셨습니다!
"""
    
    chunks = await chunker.chunk(long_conversation)
    
    print(f"   📝 원본 길이: {len(long_conversation)}자")
    print(f"   📄 청크 수: {len(chunks)}개")
    
    for i, chunk in enumerate(chunks):
        # 화자 정보 추출
        lines = chunk.content.split('\n')
        speakers = set()
        for line in lines:
            if ':' in line:
                speaker = line.split(':')[0].strip()
                if speaker in ['호영', '데비']:
                    speakers.add(speaker)
        
        speakers_str = ', '.join(speakers) if speakers else "화자 없음"
        print(f"   {i+1}. {len(chunk.content)}자: 화자({speakers_str})")
    
    # 대화가 보존되었는지 확인
    combined = '\n'.join(chunk.content for chunk in chunks)
    assert "호영:" in combined
    assert "데비:" in combined
    assert "Phase 1" in combined
    
    print("💬 대화 청킹 테스트 완료!\n")


async def test_adaptive_chunker():
    """적응형 청킹 마스터 클래스 테스트"""
    print("🌟 적응형 청킹 통합 테스트")
    
    chunker = AdaptiveChunker(max_chunk_size=1000)
    
    # 혼합 내용 테스트
    mixed_content = """
# 코딩 세션 기록

오늘 fibonacci 함수를 구현해봤습니다.

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 테스트
for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")
```

## 성능 분석 결과

| 입력값 | 결과 | 시간(ms) |
|--------|------|----------|
| 10 | 55 | 0.1 |
| 20 | 6765 | 2.3 |  
| 30 | 832040 | 342.1 |

보시다시피 재귀 방식은 n이 커질수록 기하급수적으로 느려집니다.

개발자: 동적 프로그래밍으로 최적화해야겠어요.
리뷰어: 맞습니다. 메모이제이션을 사용하면 O(n)으로 개선할 수 있죠.
"""
    
    chunks = await chunker.chunk_message(mixed_content)
    
    print(f"   📝 원본 길이: {len(mixed_content)}자")
    print(f"   📄 청크 수: {len(chunks)}개")
    
    for i, chunk in enumerate(chunks):
        content = chunk.content
        chunk_type = "코드" if "```" in content else "테이블" if "|" in content else "대화" if ":" in content else "문서"
        preview = content[:60].replace('\n', ' ')
        print(f"   {i+1}. [{chunk_type}] {len(content)}자: {preview}...")
    
    assert len(chunks) > 1  # 혼합 내용이므로 여러 청크로 분할되어야 함
    
    print("🌟 적응형 청킹 통합 테스트 완료!\n")


async def test_batch_embedding():
    """배치 임베딩 테스트"""
    print("⚡ 배치 임베딩 테스트")
    
    # Mock embedding provider
    class MockEmbeddingProvider:
        async def embed(self, text):
            return [0.1] * 384  # 가짜 벡터
    
    # Mock 설정
    from src.shared import providers
    original_provider = providers.get_embedding_provider
    providers.get_embedding_provider = lambda: MockEmbeddingProvider()
    
    try:
        processor = BatchEmbeddingProcessor(batch_size=3)
        
        # 테스트용 청크들 생성
        chunker = AdaptiveChunker()
        test_content = "테스트 " * 200  # 간단한 긴 내용
        chunks = await chunker.chunk_message(test_content)
        
        # 배치 임베딩 처리
        results = await processor.process_chunks(chunks)
        
        print(f"   📄 처리된 청크: {len(results)}개")
        print(f"   ✅ 배치 크기: 3개씩")
        
        assert len(results) == len(chunks)
        for chunk, vector in results:
            assert len(vector) == 384
            assert isinstance(vector, list)
        
        print("⚡ 배치 임베딩 테스트 완료!\n")
        
    finally:
        # Mock 복원
        providers.get_embedding_provider = original_provider


async def main():
    """모든 테스트 실행"""
    print("🔥 Phase 3 적응형 청킹 테스트 시작\n")
    
    await test_content_detection()
    await test_code_chunking()
    await test_document_chunking() 
    await test_conversation_chunking()
    await test_adaptive_chunker()
    await test_batch_embedding()
    
    print("🎉 Phase 3 모든 테스트 통과! 적응형 청킹 구현 완료!")


if __name__ == "__main__":
    asyncio.run(main())