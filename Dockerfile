FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libreoffice-nogui \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# 소스 코드 복사
COPY src/ src/
COPY data/ data/

# 데이터 디렉토리 생성
RUN mkdir -p data/sqlite

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
