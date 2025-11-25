# Knowledge Base AI Chatbot - 개발 계획서

## 1. 프로젝트 개요

### 목적
Jira/Confluence에 작성된 회사 문서를 RAG 시스템에 동기화하여, 사용자 문의에 대해 회사 문서 기반 답변을 우선 제공하고, 관련 답변이 없을 경우 범용 LLM으로 fallback하는 AI 챗봇 시스템

### 핵심 기능
1. **일일 배치 동기화**: 매일 오전 6시 Jira/Confluence 증분 업데이트
2. **RAG 기반 검색**: 벡터 검색으로 관련 문서 탐색
3. **하이브리드 응답**: RAG 우선 → LLM Fallback
4. **출처 표시**: Jira/Confluence 링크, 작성자, 업데이트 시간
5. **품질 평가**: 답변 품질 피드백 수집 시스템

---

## 2. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                   Jira / Confluence                         │
│              (회사 문서 원본 소스)                            │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Atlassian API
                           ↓
┌─────────────────────────────────────────────────────────────┐
│             Cloud Scheduler (매일 오전 6시)                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  Cloud Run Job (배치)                        │
│  1. Jira/Confluence 증분 수집 (updated > last_sync)         │
│  2. 텍스트 청킹 (RecursiveCharacterTextSplitter)            │
│  3. 임베딩 생성 (OpenAI text-embedding-3-large)             │
│  4. FAISS 인덱스 업데이트                                    │
│  5. PostgreSQL 메타데이터 업데이트                           │
│  6. Cloud Storage에 저장 (FAISS + 로그)                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   Cloud Storage                              │
│  - faiss_index/faiss.index                                  │
│  - faiss_index/metadata.pkl                                 │
│  - batch_logs/YYYY-MM-DD.log                                │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ 로드
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Cloud Run (FastAPI Main API)                   │
│                                                              │
│  [LangGraph 워크플로우]                                      │
│    1. QueryAnalyzer       (문의 분석)                        │
│    2. RAGSearcher         (벡터 검색)                        │
│    3. RelevanceChecker    (관련도 판단)                      │
│    4a. RAGResponder       (RAG 답변) ──┐                    │
│    4b. LLMFallback        (LLM 답변) ──┤                    │
│    5. ResponseFormatter   (출처 표시)  ←┘                    │
│                                                              │
│  [API 엔드포인트]                                            │
│    - POST /api/chat       (문의 답변)                        │
│    - POST /api/feedback   (품질 평가)                        │
│    - GET  /api/health     (헬스체크)                         │
│    - GET  /api/stats      (통계)                            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                Cloud SQL (PostgreSQL)                       │
│                                                              │
│  [테이블]                                                    │
│    - documents         (문서 메타데이터)                     │
│    - document_chunks   (청크 정보)                           │
│    - chat_history      (대화 이력)                           │
│    - feedback          (품질 평가)                           │
│    - sync_history      (배치 실행 이력)                      │
└─────────────────────────────────────────────────────────────┘
                           ↑
                           │
┌─────────────────────────────────────────────────────────────┐
│                 React Frontend (Vercel/Cloud Run)           │
│                                                              │
│  - 채팅 인터페이스 (메시지 입력/출력)                         │
│  - 출처 표시 (Jira/Confluence 링크)                          │
│  - 품질 평가 UI (👍/👎 피드백)                               │
│  - 통계 대시보드 (관리자용)                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 기술 스택

### Backend
- **Framework**: FastAPI 0.104+
- **Orchestration**: LangGraph (LangChain)
- **LLM**: OpenAI GPT (gpt-4o-mini, gpt-4o 선택 가능)
- **Embedding**: OpenAI text-embedding-3-large
- **Vector DB**: FAISS
- **Database**: PostgreSQL (Cloud SQL)
- **ORM**: SQLAlchemy 2.0

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: Tailwind CSS + shadcn/ui
- **State Management**: React Query + Zustand
- **HTTP Client**: Axios

### Infrastructure (GCP)
- **Main API**: Cloud Run (FastAPI)
- **Batch**: Cloud Run Job
- **Scheduler**: Cloud Scheduler
- **Storage**: Cloud Storage
- **Database**: Cloud SQL (PostgreSQL 15)
- **Secrets**: Secret Manager

### External APIs
- **Jira API**: REST API v3
- **Confluence API**: REST API v2
- **Atlassian Auth**: Basic Auth (email + API token)

---

## 4. 데이터 모델 (PostgreSQL)

### 4.1 documents (문서 메타데이터)
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(255) UNIQUE NOT NULL,  -- Jira: PROJ-123, Confluence: page_id
    doc_type VARCHAR(50) NOT NULL,         -- 'jira' or 'confluence'
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    content TEXT NOT NULL,                 -- 전체 내용
    author VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_synced_at TIMESTAMP DEFAULT NOW(),
    deleted BOOLEAN DEFAULT FALSE,         -- 소프트 삭제
    metadata JSONB,                        -- 추가 메타데이터 (labels, status 등)
    INDEX idx_doc_id (doc_id),
    INDEX idx_doc_type (doc_type),
    INDEX idx_deleted (deleted),
    INDEX idx_updated_at (updated_at)
);
```

### 4.2 document_chunks (문서 청크)
```sql
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,          -- 청크 순서
    chunk_text TEXT NOT NULL,
    embedding_vector BYTEA,                -- FAISS 인덱스 ID 매핑용
    faiss_index_id INTEGER,                -- FAISS 내 인덱스 번호
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_document_id (document_id),
    INDEX idx_faiss_index_id (faiss_index_id),
    UNIQUE(document_id, chunk_index)
);
```

### 4.3 chat_history (대화 이력)
```sql
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255),               -- 세션 구분용
    user_query TEXT NOT NULL,
    response TEXT NOT NULL,
    response_type VARCHAR(50),             -- 'rag' or 'llm_fallback'
    source_documents JSONB,                -- 사용된 문서 정보
    relevance_score FLOAT,                 -- 유사도 점수
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at),
    INDEX idx_response_type (response_type)
);
```

### 4.4 feedback (품질 평가)
```sql
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    chat_history_id INTEGER REFERENCES chat_history(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating IN (1, -1)),  -- 1: 👍, -1: 👎
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_chat_history_id (chat_history_id),
    INDEX idx_rating (rating)
);
```

### 4.5 sync_history (배치 실행 이력)
```sql
CREATE TABLE sync_history (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(50) NOT NULL,        -- 'jira' or 'confluence'
    status VARCHAR(50) NOT NULL,           -- 'success', 'failed', 'running'
    documents_added INTEGER DEFAULT 0,
    documents_updated INTEGER DEFAULT 0,
    documents_deleted INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    INDEX idx_sync_type (sync_type),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at)
);
```

---

## 5. LangGraph 워크플로우 상세

### 5.1 State 정의
```python
from typing import TypedDict, List, Literal

class ChatState(TypedDict):
    user_query: str
    analyzed_query: dict  # {intent, keywords, entities}
    search_results: List[dict]  # [{doc_id, title, content, score}]
    relevance_decision: Literal["relevant", "irrelevant"]
    response: str
    response_type: Literal["rag", "llm_fallback"]
    sources: List[dict]  # [{title, url, author, updated_at}]
```

### 5.2 Agent 개요

#### Agent 1: QueryAnalyzer
- 사용자 문의를 분석하여 검색에 필요한 정보 추출
- 의도 파악, 키워드 추출, 엔티티 추출

#### Agent 2: RAGSearcher
- FAISS 벡터 검색 + 메타데이터 필터링
- Top-K 결과 반환 (K=5)
- deleted=False 문서만 검색

#### Agent 3: RelevanceChecker
- 검색 결과가 답변 가능한지 판단
- 유사도 점수 임계값 체크 (0.7)
- LLM으로 관련성 재확인

#### Agent 4a: RAGResponder
- RAG 기반 답변 생성
- 검색된 문서를 컨텍스트로 사용
- 자연스러운 답변 생성

#### Agent 4b: LLMFallback
- 범용 LLM 답변 생성
- 회사 문서에 없는 내용 처리
- 답변 끝에 면책 문구 추가

#### Agent 5: ResponseFormatter
- 최종 답변 포맷팅
- Markdown 형식
- 출처 링크, 작성자, 업데이트 시간 표시

### 5.3 Workflow 그래프
```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(ChatState)

# 노드 추가
workflow.add_node("query_analyzer", query_analyzer)
workflow.add_node("rag_searcher", rag_searcher)
workflow.add_node("relevance_checker", relevance_checker)
workflow.add_node("rag_responder", rag_responder)
workflow.add_node("llm_fallback", llm_fallback)
workflow.add_node("response_formatter", response_formatter)

# 엣지 연결
workflow.set_entry_point("query_analyzer")
workflow.add_edge("query_analyzer", "rag_searcher")
workflow.add_edge("rag_searcher", "relevance_checker")

# 조건부 라우팅
workflow.add_conditional_edges(
    "relevance_checker",
    lambda state: state["relevance_decision"],
    {
        "relevant": "rag_responder",
        "irrelevant": "llm_fallback"
    }
)

workflow.add_edge("rag_responder", "response_formatter")
workflow.add_edge("llm_fallback", "response_formatter")
workflow.add_edge("response_formatter", END)

app = workflow.compile()
```

---

## 6. 배치 프로세스

### 6.1 배치 워크플로우
```
1. Cloud Scheduler 트리거 (매일 오전 6시)
2. Cloud Run Job 시작
3. PostgreSQL에서 last_sync 시간 조회
4. Jira API 호출 (updated > last_sync)
5. Confluence API 호출 (updated > last_sync)
6. 삭제된 문서 처리 (deleted=True)
7. 텍스트 청킹 (chunk_size=1000, chunk_overlap=200)
8. 임베딩 생성 (배치 100개씩)
9. FAISS 인덱스 업데이트
10. Cloud Storage 저장
11. PostgreSQL 업데이트
12. 완료 (실패 시 1시간 후 재시도)
```

### 6.2 재시도 로직
- 최대 3회 재시도
- 실패 시 1시간 간격으로 재시도
- sync_history 테이블에 에러 메시지 기록

---

## 7. API 엔드포인트 설계

### 7.1 POST /api/chat
채팅 문의 및 답변 생성

**Request:**
```json
{
  "query": "Jira에서 버그 리포트하는 방법은?",
  "session_id": "uuid-1234"
}
```

**Response:**
```json
{
  "response": "Jira에서 버그 리포트 방법:\n1. ...\n\n### 📚 참고 문서\n...",
  "response_type": "rag",
  "sources": [
    {
      "title": "Jira 사용 가이드",
      "url": "https://jira.company.com/...",
      "author": "홍길동",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "relevance_score": 0.87,
  "chat_id": 123
}
```

### 7.2 POST /api/feedback
답변 품질 평가

**Request:**
```json
{
  "chat_id": 123,
  "rating": 1,
  "comment": "도움이 되었습니다"
}
```

### 7.3 GET /api/health
헬스체크

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "faiss_index": "loaded",
  "last_sync": "2025-01-24T06:00:00Z"
}
```

### 7.4 GET /api/stats
통계 정보 (관리자용)

**Response:**
```json
{
  "total_documents": 1234,
  "total_chunks": 5678,
  "jira_issues": 890,
  "confluence_pages": 344,
  "last_sync": "2025-01-24T06:00:00Z",
  "chat_count_today": 45,
  "rag_response_rate": 0.72,
  "avg_feedback_rating": 0.8
}
```

---

## 8. 프론트엔드 구조 (React)

### 8.1 페이지 구조 (4페이지)
- `/` - **Landing Page**: 서비스 소개 및 마케팅 페이지
- `/chat` - **Chat**: 메인 채팅 인터페이스
- `/dashboard` - **Dashboard**: 데이터 동기화 모니터링 대시보드
- `/settings` - **Settings**: 데이터 소스 관리 (Jira/Confluence 설정)

### 8.2 페이지별 상세 구성

#### 8.2.1 Landing Page (`/`)
- **Hero Section**: 타이틀, 설명, CTA 버튼 ("Connect Your Workspace")
- **Integration Icons**: Jira, Confluence 로고
- **Features Section**: 5개 기능 카드
  - Jira & Confluence Integration
  - Real-time Incremental Sync
  - Smart Deletion Detection
  - Secure PAT Authentication
  - Cloud & Server Compatible
- **How It Works**: 3단계 설명 (Connect → Sync → Ask)
- **CTA Section**: "Try KnowledgeBot AI Free" 버튼
- **Footer**: 저작권, Terms, Privacy, Support 링크

#### 8.2.2 Chat Page (`/chat`)
- **Left Sidebar**:
  - 로고/제목 ("Knowledge AI")
  - New Chat 버튼
  - 검색 필드 (Search history)
  - 대화 목록 (채팅 기록)
  - Settings, Help & FAQ 링크
- **Main Chat Area**:
  - 대화 제목 (현재 채팅 주제)
  - 메시지 목록 (AI/사용자 구분)
  - 출처 카드 (Jira 이슈/Confluence 페이지 링크)
  - 피드백 버튼 (👍/👎)
  - 입력 필드 ("Ask anything...")

#### 8.2.3 Dashboard Page (`/dashboard`)
- **Header Navigation**: Dashboard, Data Sources, Settings, Logs, Chat help
- **Overview Cards** (4개):
  - Overall Sync Status (Healthy/Error)
  - Total Documents Synced (숫자 + 증감률)
  - Last Successful Sync (시간)
  - Next Scheduled Sync (시간)
- **Alert Banner**: 에러 발생 시 경고 메시지 ("Action Required")
- **Data Sources Section**: Jira/Confluence 상태 카드
  - 상태 표시 (Healthy/Error)
  - 동기화된 문서 수
  - 마지막 동기화 시간
- **Sync Chart**: 최근 7일 동기화 추이 (라인 차트)
- **Recent Sync Activity Table**: 타임스탬프, 이벤트 타입, 상태, 설명

#### 8.2.4 Settings Page (`/settings`)
- **Left Sidebar**: Admin Panel 메뉴
  - Dashboard, Data Sources, Settings, Analytics, Logout
- **Data Source Management**:
  - 탭: Jira | Confluence
  - Connection Status 표시기
  - Connection Settings:
    - Instance Type (Cloud/Server 라디오 버튼)
    - URL 입력 필드
    - Personal Access Token (PAT) 입력 필드
    - Test Connection 버튼
  - Synchronization Rules:
    - Incremental Sync 토글
    - Sync Frequency 드롭다운 (Every 24 hours, etc.)
    - Last Synced 정보
    - Sync Now 버튼
  - Save Changes 버튼

### 8.3 주요 컴포넌트

#### Layout 컴포넌트
- **MainLayout**: 공통 레이아웃 (Header, Footer)
- **AdminLayout**: 관리자 페이지 레이아웃 (Sidebar 포함)
- **ChatLayout**: 채팅 페이지 레이아웃 (Left Sidebar + Main Area)

#### Landing Page 컴포넌트
- **HeroSection**: 메인 타이틀, 설명, CTA
- **FeatureCard**: 기능 설명 카드
- **HowItWorks**: 단계별 설명
- **CTASection**: 행동 유도 섹션

#### Chat 컴포넌트
- **ChatSidebar**: 좌측 사이드바 (채팅 목록)
- **ChatHistory**: 채팅 기록 목록
- **ChatInterface**: 메인 채팅 UI
- **MessageList**: 메시지 목록
- **MessageItem**: 개별 메시지 (AI/사용자)
- **SourceCard**: 출처 문서 카드 (Jira/Confluence)
- **FeedbackButtons**: 👍/👎 피드백 버튼
- **ChatInput**: 메시지 입력 필드

#### Dashboard 컴포넌트
- **StatCard**: 통계 카드 (숫자 + 라벨)
- **AlertBanner**: 에러/경고 배너
- **DataSourceCard**: Jira/Confluence 상태 카드
- **SyncChart**: 동기화 추이 차트
- **SyncActivityTable**: 동기화 활동 테이블

#### Settings 컴포넌트
- **AdminSidebar**: 관리자 사이드바 메뉴
- **ConnectionSettings**: 연결 설정 폼
- **SyncRules**: 동기화 규칙 설정
- **ConnectionStatus**: 연결 상태 표시기

### 8.4 주요 기능
- 실시간 채팅 및 AI 응답
- 출처 표시 (Jira 이슈/Confluence 페이지 링크)
- 피드백 시스템 (👍/👎)
- 채팅 기록 관리 및 검색
- 데이터 소스 연결 설정 (Jira/Confluence)
- 동기화 상태 모니터링
- 동기화 스케줄 설정
- 수동 동기화 트리거

---

## 9. 배포 구조 (GCP)

### 9.1 Cloud Run (Main API)
- 이미지: `gcr.io/PROJECT_ID/knowledge-base-api:latest`
- 메모리: 2GB, CPU: 2
- Min instances: 1, Max instances: 10
- Cloud SQL 연결
- Secret Manager 통합

### 9.2 Cloud Run Job (Batch)
- 이미지: `gcr.io/PROJECT_ID/knowledge-base-batch:latest`
- Task count: 1
- Max retries: 3
- 매일 오전 6시 실행

### 9.3 Cloud Scheduler
- 스케줄: `0 6 * * *` (매일 오전 6시)
- 타임존: Asia/Seoul
- Target: Cloud Run Job

### 9.4 Cloud Storage
```
gs://knowledge-base-PROJECT_ID/
├── faiss_index/
│   ├── faiss.index
│   └── metadata.pkl
└── batch_logs/
    ├── 2025-01-24.log
    └── ...
```

---

## 10. 개발 단계

### Week 1: 프로젝트 초기 설정 및 데이터 수집
- 프로젝트 구조 생성
- PostgreSQL 스키마 생성
- Jira/Confluence API 클라이언트 구현
- 데이터 수집 스크립트

### Week 2: RAG 시스템 구축
- 텍스트 청킹
- 임베딩 생성
- FAISS 인덱스 구축
- Cloud Storage 통합

### Week 3: LangGraph 워크플로우 구현
- 5단계 에이전트 구현
- 워크플로우 연결
- End-to-end 테스트

### Week 4: API 엔드포인트 구현
- FastAPI 엔드포인트 4개
- 에러 핸들링
- 로깅 설정

### Week 5: 배치 프로세스 구현
- 증분 동기화
- FAISS 인덱스 업데이트
- 재시도 로직

### Week 6: 프론트엔드 개발 (React)
- 채팅 UI
- 피드백 시스템
- API 통합

### Week 7: 통계 대시보드 (관리자용)
- 통계 컴포넌트
- 차트 구현
- 관리자 페이지

### Week 8: GCP 배포
- Cloud SQL 설정
- Cloud Run 배포
- Cloud Scheduler 설정
- 프론트엔드 배포

### Week 9: 테스트 및 최적화
- 단위/통합 테스트
- 부하 테스트
- 성능 최적화

### Week 10: 문서화 및 런칭
- README, API 문서
- 사용자 가이드
- 베타 테스트
- 정식 런칭 🚀

---

## 11. 디렉토리 구조

```
knowledge-base-ai-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   ├── core/
│   │   │   ├── agents/
│   │   │   ├── workflow/
│   │   │   └── services/
│   │   └── utils/
│   ├── batch/
│   ├── tests/
│   ├── scripts/
│   ├── Dockerfile.api
│   ├── Dockerfile.batch
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/            # 레이아웃 컴포넌트
│   │   │   │   ├── MainLayout.tsx
│   │   │   │   ├── AdminLayout.tsx
│   │   │   │   ├── ChatLayout.tsx
│   │   │   │   └── Header.tsx
│   │   │   ├── landing/           # Landing Page 컴포넌트
│   │   │   │   ├── HeroSection.tsx
│   │   │   │   ├── FeatureCard.tsx
│   │   │   │   ├── HowItWorks.tsx
│   │   │   │   └── CTASection.tsx
│   │   │   ├── chat/              # Chat 컴포넌트
│   │   │   │   ├── ChatSidebar.tsx
│   │   │   │   ├── ChatHistory.tsx
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── MessageItem.tsx
│   │   │   │   ├── SourceCard.tsx
│   │   │   │   ├── FeedbackButtons.tsx
│   │   │   │   └── ChatInput.tsx
│   │   │   ├── dashboard/         # Dashboard 컴포넌트
│   │   │   │   ├── StatCard.tsx
│   │   │   │   ├── AlertBanner.tsx
│   │   │   │   ├── DataSourceCard.tsx
│   │   │   │   ├── SyncChart.tsx
│   │   │   │   └── SyncActivityTable.tsx
│   │   │   └── settings/          # Settings 컴포넌트
│   │   │       ├── AdminSidebar.tsx
│   │   │       ├── ConnectionSettings.tsx
│   │   │       ├── SyncRules.tsx
│   │   │       └── ConnectionStatus.tsx
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── stores/
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx
│   │   │   ├── ChatPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   └── types/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── stitch/                    # UI 디자인 목업
│   │   ├── landing_page.png
│   │   ├── chat.png
│   │   ├── dashboard.png
│   │   └── setting.png
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   └── USER_GUIDE.md
├── README.md
├── CLAUDE.md
└── .gitignore
```

---

## 12. 환경 변수

### backend/.env
```bash
# PostgreSQL (Cloud SQL)
DATABASE_URL=postgresql://user:password@/dbname?host=/cloudsql/...

# ========================================
# API Provider Configuration
# ========================================

# Option 1: OpenAI GPT (https://platform.openai.com/api-keys)
# Recommended models: gpt-4o-mini (fast/cheap), gpt-4o (best quality)
OPENAI_API_KEY=sk-proj-your-openai-api-key-here

# Option 2: Anthropic Claude (https://console.anthropic.com/)
# Recommended models: claude-3-5-haiku (fast/cheap), claude-3-5-sonnet (best quality)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# ========================================
# Application Settings
# ========================================

# Default API provider: 'openai' or 'anthropic'
DEFAULT_PROVIDER=openai

# Default model name
# OpenAI: gpt-4o-mini, gpt-4o, gpt-4-turbo, gpt-3.5-turbo
# Anthropic: claude-3-5-haiku-20241022, claude-3-5-sonnet-20241022
DEFAULT_MODEL=gpt-4o-mini

# Jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-token

# Confluence
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your-confluence-token

# Google Cloud Storage Configuration (Optional)
GCS_BUCKET_NAME=knowledge-base-PROJECT_ID
GOOGLE_APPLICATION_CREDENTIALS=

# App Config
APP_ENV=production
DEBUG=False
LOG_LEVEL=INFO
RELEVANCE_THRESHOLD=0.7
TOP_K_RESULTS=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

---

## 13. 추후 개선 사항 (Phase 2)

### 인증 및 권한
- Google OAuth 2.0 통합
- Jira/Confluence 권한 상속
- Admin 역할 관리

### 고급 기능
- 멀티턴 대화 (대화 컨텍스트 유지)
- 문서 요약 기능
- 스트리밍 응답 (SSE)
- 음성 입력/출력
- 다국어 지원

### 모니터링 및 분석
- Cloud Monitoring 대시보드
- 사용자 행동 분석
- A/B 테스트

### 확장성
- Slack/Teams 봇 통합
- 모바일 앱 (React Native)
- GraphQL API

---

## 14. 예상 비용 (월간, GCP)

| 서비스 | 월간 비용 (USD) |
|--------|----------------|
| Cloud Run (Main API) | $30 |
| Cloud Run Job (Batch) | $5 |
| Cloud SQL (PostgreSQL) | $15 |
| Cloud Storage | $1 |
| Cloud Scheduler | $0.10 |
| OpenAI GPT (gpt-4o-mini) | $10 |
| OpenAI Embedding | $1 |
| **총합** | **~$62** |

---

## 15. 성공 지표 (KPI)

| 지표 | 목표 |
|------|------|
| **RAG 응답 비율** | 70% 이상 |
| **긍정 피드백 비율** | 80% 이상 |
| **평균 응답 시간** | 3초 이내 |
| **배치 성공률** | 95% 이상 |
| **문서 커버리지** | 90% 이상 |
| **일일 활성 사용자** | 50명 이상 |

---

**작성일**: 2025-01-24
**프로젝트 위치**: `/Users/sunchulkim/src/knowledge-base-ai-chatbot/`
**작성자**: Claude Code
