# CS Cost Optimizer Agent - Production Code

고객센터 운영 비용 최적화 에이전트. FAQ 자동 응답으로 상담원 투입 건수를 최소화하고, 처리 건수 대비 운영 비용을 지속적으로 낮추는 AI 에이전트.

## 아키텍처

```
클라이언트 (웹채팅, 카카오톡, 전화, 이메일)
       ↓ HTTP/SSE
   FastAPI + LangGraph
       ↓
Node 1: 입력 파싱
Node 2: 질문 분류 (LLM)
Node 3: JSON 파싱
Node 4: FAQ 검색 + 관련도 평가 (최대 3회)
Node 5: 자동 처리 판단
   ├─ True: Node 6 → Node 7 → 자동 답변 출력
   └─ False: Node 9 → 상담원 이관 안내
       ↓
외부 시스템 (ChromaDB, PostgreSQL, 상담원 업무 시스템, 알림 서비스)
```

## 디렉토리 구조

```
cs-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 진입점
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py            # 환경 설정
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logger.py              # 구조화 로깅
│   │   └── exceptions.py          # 커스텀 예외
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py               # LangGraph 상태
│   │   ├── workflow.py            # 워크플로우 조립
│   │   └── nodes/                 # 각 노드 구현
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py              # API 엔드포인트
│   │   └── schemas.py             # Pydantic 스키마
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py              # SQLAlchemy 모델
│   │   └── repository.py          # 데이터 접근
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── faq_kb.py              # FAQ 검색
│   │   └── notifier.py            # 알림 발송
│   └── monitoring/
│       ├── __init__.py
│       └── metrics.py             # Prometheus 메트릭
├── tests/
│   ├── unit/                      # 단위 테스트
│   ├── integration/               # 통합 테스트
│   └── scenarios/                 # 시나리오 테스트
├── requirements.txt               # 의존성
├── .env.example                   # 환경 샘플
├── Dockerfile                     # Docker 이미지
├── docker-compose.yml             # Compose 설정
└── README_PROD.md                # 본 문서
```

## 소스 코드 설명

### 상태 정의 (graph/state.py)

LangGraph StateGraph의 상태 스키마. 모든 노드의 입출력을 전달.

주요 필드:
- query: 고객 질문 텍스트
- inquiry_channel: 문의 채널 (웹채팅, 카카오톡, 전화, 이메일)
- complexity: 복잡도 (low/high)
- category: 카테고리
- top_score: FAQ 검색 최고 관련도 점수
- auto_processable: 자동 처리 가능 여부
- generated_answer: LLM 생성 답변
- saved_cost: 절감 비용
- agent_id, agent_name, queue_position: 상담원 정보

### 워크플로우 (graph/workflow.py)

LangGraph StateGraph 조립. 노드와 조건부 엣지 정의.

흐름:
1. START → classify → parse_json → faq_search → decide
2. decide 조건:
   - score >= 75 AND complexity == "low": answer_gen → cost_agg → END
   - 아니면: agent_assign → END

### 노드 구현 (graph/nodes/)

각 노드별 독립적 함수로 구현:

- classifier.py: Groq LLM으로 질문 분류
- json_parser.py: LLM 출력 JSON 파싱
- faq_search.py: FAQ 검색 + 관련도 평가 루프 (MOCK)
- decider.py: 자동 처리 판단 로직
- answer_gen.py: Groq LLM으로 자동 답변 생성
- cost_agg.py: 절감 비용 계산 (MOCK)
- agent_assign.py: 상담원 배정 (MOCK)

### API 엔드포인트 (api/routes.py)

FastAPI 라우터:

- POST /v1/chat/stream: SSE 스트리밍 응답
- GET /v1/metrics/daily: 당일 집계 조회
- GET /health: 헬스체크

### 데이터베이스 (db/)

models.py: SQLAlchemy ORM 모델
- processing_history: 처리 이력 (query_hash, category, complexity, saved_cost 등)
- daily_cost_summary: 일일 집계 (total_inquiries, auto_processed, total_saved 등)

repository.py: 데이터 접근 계층 (MOCK)

### 테스트 (tests/)

unit/: 각 노드별 단위 테스트
- test_json_parser.py: JSON 파싱 로직
- test_decider.py: 자동 처리 판단 로직
- test_cost_agg.py: 비용 집계 로직
- test_agent_assign.py: 상담원 배정 로직

integration/: 전체 워크플로우 통합 테스트
- test_workflow.py: 자동 답변/이관 경로

scenarios/: 시나리오 기반 E2E 테스트
- test_scenarios.py: SC-01~SC-04

## 설치 및 실행

### 필수 사항

- Python 3.11+
- Groq API 키

### 설치

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 환경 설정

```bash
cp .env.example .env
# .env 파일에서 GROQ_API_KEY 설정
```

### 로컬 실행

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버: http://localhost:8000

### Docker 실행

```bash
docker-compose up -d
```

## API 사용 예시

### 채팅 요청

```bash
curl -X POST http://localhost:8000/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-test-key" \
  -d '{
    "query": "충전 케이블 연결 방법",
    "inquiry_channel": "웹채팅",
    "mock_preset": "default"
  }'
```

### SSE 응답 (자동 답변)

```
event: message
data: {"type": "token", "content": "전원 버튼을"}

event: metadata
data: {
  "process_type": "auto",
  "category": "제품사용",
  "top_score": 88,
  "saved_cost": 28000
}

event: done
data: {}
```

## 테스트 실행

```bash
# 단위 테스트
pytest tests/unit/ -v

# 통합 테스트
pytest tests/integration/ -v

# 전체 테스트
pytest tests/ -v --cov=app
```

## 주요 기능

1. **질문 분류**: Groq LLM으로 복잡도/카테고리 자동 분류
2. **FAQ 검색**: 의미 검색 + 관련도 평가 루프 (최대 3회)
3. **자동 처리 판단**: score >= 75 AND complexity == "low"
4. **자동 답변**: Groq LLM이 FAQ 기반 200자 이내 답변 생성
5. **비용 절감**: 1건당 28,000원 계산 및 누적
6. **상담원 배정**: 복잡도 기반 우선순위 산정
7. **실시간 모니터링**: Prometheus 메트릭 수집

## 성능 목표

| 항목 | 목표 |
|------|------|
| 자동 답변 응답 | 8초 이내 |
| 상담원 이관 | 20초 이내 |
| 자동 처리율 | 70% 이상 |
| 오답률 | 5% 이하 |
| 동시 처리 | 100 TPS |

## 제약사항

- MOCK 프리셋 기반 FAQ 검색/상담원 배정/비용 집계
- ChromaDB/PostgreSQL/상담원 시스템 연동은 스텁

## 추후 개선

- ChromaDB 실제 벡터 검색 통합
- PostgreSQL 실제 DB 연동
- 상담원 시스템 REST API 연동
- Slack/이메일 알림 구현
- Grafana 모니터링 대시보드
