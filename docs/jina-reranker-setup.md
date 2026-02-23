# Jina Reranker 설치 가이드

메모리 검색 결과의 정확도를 높이기 위한 Jina Reranker 로컬 서버 설치 가이드입니다.

## 개요

- **모델**: `jinaai/jina-reranker-v2-base-multilingual`
- **역할**: 벡터 검색 결과를 질문과의 관련성 기준으로 재정렬
- **서버 포트**: `7998` (기본값)
- **필수 여부**: 선택사항 (미설치 시 벡터 유사도 + 최신성 점수로 fallback)

## 1. 사전 요구사항

```bash
# Python 3.10+
python --version

# GPU 사용 시 (권장): CUDA 11.8+ 설치 확인
nvidia-smi
```

## 2. 설치

### 방법 A: venv 환경 (권장)

```bash
# 별도 가상환경 생성
python -m venv reranker-venv
source reranker-venv/bin/activate  # Linux/Mac

# 패키지 설치
pip install fastapi uvicorn transformers torch

# GPU 사용 시 (CUDA)
pip install torch --index-url https://download.pytorch.org/whl/cu118

# 모델 다운로드 (최초 1회, ~1.1GB)
python -c "from transformers import AutoModelForSequenceClassification, AutoTokenizer; \
AutoModelForSequenceClassification.from_pretrained('jinaai/jina-reranker-v2-base-multilingual', trust_remote_code=True); \
AutoTokenizer.from_pretrained('jinaai/jina-reranker-v2-base-multilingual', trust_remote_code=True)"
```

### 방법 B: Docker

```bash
docker run -d \
  --name jina-reranker \
  -p 7998:7998 \
  -v reranker-cache:/root/.cache \
  --gpus all \
  ghcr.io/huggingface/text-embeddings-inference:latest \
  --model-id jinaai/jina-reranker-v2-base-multilingual \
  --port 7998
```

## 3. 서버 실행 스크립트

`reranker_server.py` 파일을 생성합니다:

```python
"""Jina Reranker 로컬 서버"""
import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer

app = FastAPI(title="Jina Reranker Server")

MODEL_NAME = "jinaai/jina-reranker-v2-base-multilingual"
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading model on {device}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, trust_remote_code=True
).to(device)
model.eval()
print("Model loaded!")


class RerankRequest(BaseModel):
    model: str = MODEL_NAME
    query: str
    documents: list[str]
    top_n: int | None = None


class RerankResult(BaseModel):
    index: int
    relevance_score: float


class RerankResponse(BaseModel):
    model: str
    results: list[RerankResult]


@app.post("/rerank")
async def rerank(request: RerankRequest) -> RerankResponse:
    if not request.documents:
        return RerankResponse(model=request.model, results=[])

    top_n = request.top_n or len(request.documents)
    pairs = [[request.query, doc] for doc in request.documents]

    with torch.no_grad():
        inputs = tokenizer(
            pairs, padding=True, truncation=True,
            max_length=512, return_tensors="pt"
        ).to(device)
        scores = model(**inputs).logits.squeeze(-1).tolist()

    if isinstance(scores, float):
        scores = [scores]

    indexed_scores = [(i, s) for i, s in enumerate(scores)]
    indexed_scores.sort(key=lambda x: x[1], reverse=True)

    results = [
        RerankResult(index=idx, relevance_score=score)
        for idx, score in indexed_scores[:top_n]
    ]

    return RerankResponse(model=request.model, results=results)


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_NAME, "device": device}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7998)
```

### 실행

```bash
# 포그라운드
python reranker_server.py

# 백그라운드 (nohup)
nohup python reranker_server.py > /tmp/reranker.log 2>&1 &

# systemd 서비스 등록 (Linux)
# /etc/systemd/system/jina-reranker.service 참고
```

## 4. 연동 설정

`.env` 파일에 추가:

```env
RERANKER_URL=http://localhost:7998
RERANKER_MODEL=jinaai/jina-reranker-v2-base-multilingual
```

## 5. 동작 확인

```bash
# 헬스 체크
curl http://localhost:7998/health

# 리랭킹 테스트
curl -X POST http://localhost:7998/rerank \
  -H "Content-Type: application/json" \
  -d '{
    "query": "내일 회의 일정",
    "documents": [
      "내일 오후 2시에 품질 미팅이 있습니다",
      "오늘 점심은 김치찌개를 먹었다",
      "금요일에 아키텍처 리뷰 회의 예정"
    ],
    "top_n": 3
  }'
```

예상 응답:

```json
{
  "model": "jinaai/jina-reranker-v2-base-multilingual",
  "results": [
    {"index": 0, "relevance_score": 0.85},
    {"index": 2, "relevance_score": 0.72},
    {"index": 1, "relevance_score": 0.05}
  ]
}
```

## 6. 리소스 요구사항

| 항목 | CPU 모드 | GPU 모드 |
|------|----------|----------|
| RAM | ~2GB | ~1GB |
| VRAM | - | ~2GB |
| 모델 크기 | ~1.1GB | ~1.1GB |
| 응답 속도 (10건) | ~200ms | ~50ms |

## 7. 문제 해결

### Reranker 서버 연결 실패

```
⚠️  Reranker 서버 연결 실패 - 리랭킹 건너뜀
```

서버가 꺼져 있어도 메모리 검색은 정상 동작합니다 (벡터 유사도 + 최신성 점수 fallback).

### CUDA out of memory

GPU 메모리 부족 시 CPU 모드로 자동 전환됩니다. 또는 `max_length`를 256으로 줄여볼 수 있습니다.

### trust_remote_code 경고

Jina 모델은 커스텀 코드가 포함되어 있어 `trust_remote_code=True`가 필요합니다. 공식 Hugging Face 모델이므로 안전합니다.
