# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

# 비루트 사용자 생성 (보안)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# builder에서 설치된 패키지 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 소스 코드 복사
COPY app/ ./app/

# 비루트 사용자로 전환
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
