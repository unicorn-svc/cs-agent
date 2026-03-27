# 고객센터 운영 비용 최적화 에이전트

FAQ 자동 응답으로 상담원 투입 건수를 최소화하고,
처리 건수 대비 운영 비용을 지속적으로 낮추는 비용 절감 에이전트

## 아키텍처

```mermaid
graph TB
    subgraph Client["클라이언트"]
        WEB[웹채팅]
        KAKAO[카카오톡]
        TEL[전화/이메일]
    end

    subgraph MCP["MCP 서버 (FastAPI + Streaming HTTP)"]
        API["/v1/chat/stream<br/>POST Endpoint"]
        subgraph LG["LangGraph StateGraph"]
            N1[Node 1: 시작<br/>입력 파싱]
            N2[Node 2: 질문 분류<br/>LLM - Groq]
            N3[Node 3: JSON 파싱<br/>complexity, category]
            N4[Node 4: FAQ 검색<br/>+ 관련도 평가 루프]
            N5{Node 5: 자동처리<br/>가능 여부 판단}
            N6[Node 6: 자동 답변 생성<br/>LLM - Groq]
            N7[Node 7: 비용 절감 집계]
            N8[Node 8: 자동 답변 출력]
            N9[Node 9: 상담원 배정]
            N10[Node 10: 상담원 이관 안내]
        end
    end

    subgraph EXT["외부 시스템"]
        FAQ_DB[(FAQ 지식베이스<br/>ChromaDB)]
        COST_DB[(비용 집계 DB<br/>PostgreSQL)]
        AGENT_SYS[상담원 업무 시스템]
    end

    Client -->|HTTP/SSE| API
    API --> N1 --> N2 --> N3 --> N4 --> N5
    N5 -->|"score>=75 AND low"| N6 --> N7 --> N8
    N5 -->|"그 외"| N9 --> N10
    N4 -.->|의미 검색| FAQ_DB
    N7 -.->|집계 저장| COST_DB
    N9 -.->|배정 요청| AGENT_SYS
```

### 데이터 흐름

```
고객 질문 입력
  → [InputParser] inquiry_channel, query, mock_preset 파싱
  → [QuestionClassifier] LLM → {"complexity": "low/high", "category": "카테고리명"}
  → [JSONParser] complexity, category 변수 분리
  → [FAQSearchEngine] 의미 검색 → 관련도 평가 → 90점 미만 시 질문 수정 재검색 (최대 3회)
  → [AutoProcessDecider] top_score>=75 AND complexity=low ?
      → true: [AutoAnswerGenerator] LLM → 200자 이내 답변
              [CostAggregator] 28,000원/건 절감 집계
              [AutoAnswerOutput] SSE 스트리밍 출력
      → false: [AgentAssigner] 복잡도/긴급도 기반 우선순위 배정
               [EscalationOutput] 대기 시간 + 배정 상담원 안내
```

## 디렉토리 구조

```
cs-agent/
├── app/
│   ├── main.py                  # FastAPI 엔트리포인트
│   ├── graph/
│   │   ├── state.py             # LangGraph 상태 정의 (AgentState TypedDict)
│   │   ├── workflow.py          # 워크플로우 그래프 조립 (StateGraph)
│   │   └── nodes/
│   │       ├── classifier.py    # Node 2: 질문 분류 (LLM - Groq)
│   │       ├── json_parser.py   # Node 3: JSON 파싱
│   │       ├── faq_search.py    # Node 4: FAQ 검색 + 관련도 평가 루프
│   │       ├── decider.py       # Node 5: 자동처리 가능 여부 판단
│   │       ├── answer_gen.py    # Node 6: 자동 답변 생성 (LLM - Groq)
│   │       ├── cost_agg.py      # Node 7: 비용 절감 집계
│   │       ├── auto_output.py   # Node 8: 자동 답변 출력 포맷
│   │       ├── agent_assign.py  # Node 9: 상담원 배정
│   │       └── escalation.py    # Node 10: 상담원 이관 안내
│   ├── tools/
│   │   ├── faq_kb.py            # FAQ 지식베이스 (Real: ChromaDB / Mock)
│   │   ├── cost_tracker.py      # 비용 집계 (Real: PostgreSQL / Mock)
│   │   ├── agent_queue.py       # 상담원 대기열 (Real: REST API / Mock)
│   │   └── notifier.py          # 알림 발송 (Real: Webhook / Mock)
│   ├── api/
│   │   ├── routes.py            # API 엔드포인트 (SSE 스트리밍, 메트릭, 헬스체크)
│   │   └── schemas.py           # Pydantic 입출력 스키마
│   ├── config/
│   │   └── settings.py          # 환경 설정 (API Key, 임계값 등)
│   └── monitoring/
│       └── metrics.py           # Prometheus 메트릭 수집
├── tests/
│   ├── conftest.py              # 테스트 공통 fixture
│   ├── unit/                    # 단위 테스트
│   │   ├── test_json_parser.py
│   │   ├── test_decider.py
│   │   ├── test_cost_agg.py
│   │   ├── test_agent_assign.py
│   │   ├── test_faq_search.py
│   │   └── test_schemas.py
│   ├── integration/             # 통합 테스트
│   │   ├── test_workflow.py
│   │   └── test_api.py
│   └── scenarios/               # 시나리오 테스트
│       └── test_scenarios.py
├── output/                      # DSL, 개발계획서, 시나리오 문서
├── Dockerfile                   # Multi-stage Docker 빌드
├── docker-compose.yml           # 로컬/스테이징 멀티 컨테이너
├── prometheus.yml               # Prometheus 수집 설정
├── pyproject.toml               # 프로젝트 의존성 및 빌드 설정
├── .env.example                 # 환경 변수 템플릿
└── .gitignore
```

## 소스 코드 설명

### 주요 모듈

| 모듈 | 파일 | 설명 |
|------|------|------|
| 워크플로우 | `app/graph/workflow.py` | LangGraph StateGraph 조립. DSL 노드/엣지를 1:1 매핑 |
| 상태 정의 | `app/graph/state.py` | 전체 워크플로우 상태 스키마 (AgentState TypedDict) |
| 질문 분류 | `app/graph/nodes/classifier.py` | Groq LLM으로 복잡도/카테고리 분류 |
| FAQ 검색 | `app/graph/nodes/faq_search.py` | 의미 검색 + 관련도 평가 루프 (최대 3회) |
| 자동 답변 | `app/graph/nodes/answer_gen.py` | Groq LLM으로 200자 이내 답변 생성 |
| 비용 집계 | `app/graph/nodes/cost_agg.py` | 건당 28,000원 절감 비용 계산 및 누적 |
| 상담원 배정 | `app/graph/nodes/agent_assign.py` | 복잡도 기반 우선순위 결정 및 대기열 등록 |
| API 서버 | `app/api/routes.py` | FastAPI SSE 스트리밍, 메트릭, 헬스체크 엔드포인트 |

### 처리 흐름

1. `POST /v1/chat/stream` 요청 수신
2. `workflow.invoke()` → LangGraph StateGraph 실행
3. Node 2: LLM(Groq)으로 질문 복잡도/카테고리 분류
4. Node 3: LLM 출력 JSON 파싱
5. Node 4: FAQ 벡터 검색 + 관련도 평가 (90점 미만 시 최대 3회 재검색)
6. Node 5: 분기 판단 (score >= 75 AND complexity == "low")
7. 자동 처리 경로: Node 6 → 7 → 8 (답변 생성 → 비용 집계 → SSE 출력)
8. 이관 경로: Node 9 → 10 (상담원 배정 → 이관 안내)

### Mock/Real 전환

`.env` 파일의 `USE_MOCK=true/false`로 전환.
Mock 모드에서는 외부 시스템(ChromaDB, PostgreSQL, 상담원 시스템) 없이 동작.
각 도구 모듈(`tools/`)에 Real 클래스와 Mock 클래스가 공존하며,
`settings.use_mock` 값에 따라 런타임 전환.

## 가상환경 설정 및 실행 방법

### 사전 요구사항

- Python 3.11 이상
- (선택) Docker 24.x, Docker Compose

### 로컬 실행

```bash
# 1. 가상환경 생성 및 활성화
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 2. 의존성 설치
pip install -e ".[dev]"

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일에서 GROQ_API_KEY 설정

# 4. 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. 테스트 실행
pytest tests/ -v
```

### Docker 실행

```bash
# 전체 스택 기동 (app + chromadb + postgres + prometheus + grafana)
docker-compose up -d

# 앱만 빌드 및 실행
docker build -t cs-agent .
docker run -p 8000:8000 --env-file .env cs-agent
```

### API 테스트

> 상세 테스트 방법은 [테스트 챗봇 수행 가이드](#테스트-챗봇-수행-가이드) 참조.

```bash
# 헬스체크
curl http://localhost:8000/health

# 채팅 (SSE 스트리밍, X-Api-Key 인증 필요)
curl -N -X POST http://localhost:8000/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: cs-agent-api-key-2026" \
  -d '{"query": "충전 케이블 연결 방법을 알려주세요", "inquiry_channel": "웹채팅"}'

# 당일 메트릭
curl http://localhost:8000/v1/metrics/daily \
  -H "X-Api-Key: cs-agent-api-key-2026"

# 월별 메트릭
curl http://localhost:8000/v1/metrics/monthly?year=2026&month=3 \
  -H "X-Api-Key: cs-agent-api-key-2026"
```

## 테스트 챗봇 수행 가이드

### 1. Streamlit 챗봇 UI

Streamlit 기반 웹 챗봇 UI(`chatbot.py`)로 FAQ 자동 응답 에이전트를 시각적으로 테스트 가능.

#### 사전 준비

```bash
# 1. Streamlit 설치 (프로젝트 의존성에 미포함, 별도 설치 필요)
pip install streamlit

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일에서 아래 값 설정:
#   GROQ_API_KEY=<실제 Groq API 키>
#   API_KEY=cs-agent-api-key-2026   ← chatbot.py에 하드코딩된 값과 일치 필요
#   USE_MOCK=true                    ← Mock 모드로 외부 시스템 없이 테스트

# 3. FastAPI 서버 실행 (별도 터미널)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> **참고**: `chatbot.py`의 `API_KEY` 상수(`cs-agent-api-key-2026`)와
> `.env` 파일의 `API_KEY` 값이 일치해야 인증 통과.
> curl로 직접 테스트 시에도 동일한 키를 `X-Api-Key` 헤더에 사용.

#### 챗봇 UI 실행

```bash
streamlit run chatbot.py
```

실행 후 브라우저에서 `http://localhost:8501` 접속.

#### UI 구성

| 영역 | 기능 |
|------|------|
| 사이드바 — 문의 채널 | 웹채팅, 카카오톡, 전화, 이메일 중 선택 |
| 사이드바 — API 서버 | 백엔드 서버 URL 변경 (기본: `http://localhost:8000`) |
| 사이드바 — 서버 상태 확인 | `/health` 엔드포인트로 서버 연결 상태 확인 |
| 사이드바 — 대화 초기화 | 채팅 히스토리 초기화 |
| 메인 — 채팅 입력 | 하단 입력창에 고객 질문 입력 |
| 메인 — 응답 표시 | SSE 스트리밍으로 실시간 답변 렌더링 |
| 메인 — 메타데이터 | 자동 답변 시 카테고리/복잡도/검색 시도/절감 비용 표시,  |
|  | 이관 시 담당 상담원/대기 순번/예상 대기 시간 표시 |

#### 테스트 시나리오별 예시 질문

| 시나리오 | 예시 질문 | 예상 결과 |
|---------|----------|----------|
| FAQ 자동 응답 | "충전 케이블 연결 방법을 알려주세요" | 자동 답변 + 28,000원 절감 |
| 상담원 이관 | "환불 분쟁으로 인한 법적 소송 관련 상담이 필요합니다" | 상담원 배정 안내 |
| 간단 제품 문의 | "배터리 잔량 확인 방법이 궁금해요" | 자동 답변 |
| 복잡 문의 | "제품 불량으로 교환 후 재불량이 발생했습니다" | 상담원 이관 |

### 2. curl을 이용한 API 직접 테스트

서버 실행 상태에서 터미널로 직접 API 호출 가능.

```bash
# 서버 상태 확인
curl http://localhost:8000/health

# FAQ 자동 응답 테스트 (SSE 스트리밍)
curl -N -X POST http://localhost:8000/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: cs-agent-api-key-2026" \
  -d '{"query": "충전 케이블 연결 방법을 알려주세요", "inquiry_channel": "웹채팅"}'

# 상담원 이관 테스트
curl -N -X POST http://localhost:8000/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: cs-agent-api-key-2026" \
  -d '{"query": "환불 분쟁으로 인한 법적 소송 관련 상담이 필요합니다", "inquiry_channel": "전화"}'

# 당일 메트릭 조회
curl http://localhost:8000/v1/metrics/daily \
  -H "X-Api-Key: cs-agent-api-key-2026"

# 월별 메트릭 조회
curl http://localhost:8000/v1/metrics/monthly?year=2026&month=3 \
  -H "X-Api-Key: cs-agent-api-key-2026"
```

#### SSE 응답 형식

```
event: message
data: {"type": "token", "content": "답변 텍스트 조각"}

event: metadata
data: {"process_type": "auto", "category": "제품사용", "saved_cost": 28000, ...}

event: done
data: {}
```

### 3. 자동화 테스트 (pytest)

Mock 모드(`USE_MOCK=true`)에서 외부 시스템 없이 전체 테스트 수행 가능.

```bash
# 전체 테스트 실행
pytest tests/ -v

# 단위 테스트만 실행
pytest tests/unit/ -v

# 통합 테스트만 실행
pytest tests/integration/ -v

# 시나리오 테스트만 실행
pytest tests/scenarios/ -v

# 커버리지 포함 실행
pytest tests/ --cov=app --cov-report=term-missing

# 특정 마커로 실행
pytest -m unit -v
pytest -m integration -v
pytest -m scenario -v
```

#### 시나리오 테스트 목록

| ID | 시나리오 | 검증 항목 |
|----|---------|----------|
| SC-01 | 단순 FAQ 자동 처리 | `auto_processable=True`, 절감 비용 > 0, 답변 생성 |
| SC-02 | 고복잡도 상담원 이관 | `auto_processable=False`, 상담원 배정, 우선순위 high |
| SC-03 | FAQ 재검색 루프 | 검색 시도 횟수 >= 1 (최대 3회 반복) |
| SC-04 | 자동 처리율 70% 검증 | 100건 중 자동 처리율 60% 이상 달성 |

### 4. Mock 모드 활용

`.env` 파일의 `USE_MOCK=true` 설정 시 외부 시스템(ChromaDB, PostgreSQL, 상담원 시스템) 없이 동작.

| Mock Preset | 동작 |
|-------------|------|
| `default` | 정상 FAQ 검색 결과 반환 (자동 답변 경로) |
| `empty` | FAQ 검색 결과 없음 (이관 경로) |
| `error` | 고복잡도 분류 (이관 경로) |
| `timeout` | 타임아웃 시뮬레이션 |

```bash
# Mock preset을 지정한 curl 테스트
curl -N -X POST http://localhost:8000/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: cs-agent-api-key-2026" \
  -d '{"query": "테스트 질문", "inquiry_channel": "웹채팅", "mock_preset": "empty"}'
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|-------|------|------|
| POST | `/v1/chat/stream` | 고객 질문 처리 (SSE 스트리밍) |
| GET | `/v1/metrics/daily` | 당일 처리 현황 및 절감 비용 조회 |
| GET | `/v1/metrics/monthly` | 월별 집계 보고서 조회 |
| GET | `/health` | 서비스 헬스체크 |
| GET | `/metrics` | Prometheus 메트릭 |

## MCP 서버 Claude Code 추가 방법

### Streaming HTTP

```bash
claude mcp add --transport http -s project cs-cost-optimizer http://localhost:8000
```

### stdio

```bash
claude mcp add-json cs-cost-optimizer '{
  "type": "stdio",
  "command": "python",
  "args": ["-m", "uvicorn", "app.main:app", "--port", "8000"],
  "env": {
    "GROQ_API_KEY": "your_groq_api_key",
    "USE_MOCK": "true"
  }
}' -s project
```

## 환경 변수

| 변수명 | 설명 | 기본값 |
|-------|------|-------|
| `GROQ_API_KEY` | Groq API 인증 키 | (필수) |
| `API_KEY` | 서비스 API 인증 키 | (선택) |
| `USE_MOCK` | Mock 모드 사용 여부 | `true` |
| `CHROMADB_HOST` | ChromaDB 호스트 | `localhost` |
| `POSTGRES_DSN` | PostgreSQL 연결 문자열 | `postgresql://csagent:csagent@localhost:5432/csagent` |
| `FAQ_SCORE_THRESHOLD` | FAQ 자동처리 점수 임계값 | `75` |
| `MAX_SEARCH_ATTEMPTS` | 최대 재검색 횟수 | `3` |
| `AUTO_RATE_ALERT_THRESHOLD` | 자동 처리율 알림 임계값 (%) | `60` |

## 기술스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.11+ |
| AI 오케스트레이션 | LangChain 0.3.x |
| 워크플로우 | LangGraph 0.2.x |
| API 서버 | FastAPI 0.115.x |
| LLM | Groq (meta-llama/llama-4-scout-17b-16e-instruct) |
| 벡터 DB | ChromaDB |
| 집계 DB | PostgreSQL |
| 모니터링 | Prometheus + Grafana |
| 컨테이너 | Docker + Docker Compose |
