# Knowledge Base AI Chatbot

Jira/Confluence 문서 기반 RAG(Retrieval-Augmented Generation) AI 챗봇 시스템

## 프로젝트 개요

회사 내부 Jira/Confluence에 작성된 문서를 RAG 시스템에 동기화하여, 사용자 문의에 대해 회사 문서 기반 답변을 우선 제공하고, 관련 답변이 없을 경우 범용 LLM으로 fallback하는 AI 챗봇 시스템입니다.

## 주요 기능

- **Jira/Confluence 데이터 수집**: 이슈 및 페이지 자동 수집
- **증분 동기화**: 변경된 문서만 업데이트
- **삭제 감지**: 원본에서 삭제된 문서 soft-delete 처리
- **PAT 인증 지원**: Personal Access Token (Bearer 토큰) 인증
- **Cloud/Server 지원**: Atlassian Cloud 및 로컬 서버 모두 지원
- **RAG 기반 답변**: 회사 문서 기반 정확한 답변 제공
- **LLM Fallback**: 관련 문서 없을 시 일반 지식 기반 답변
- **관리자 대시보드**: 동기화 상태 및 통계 모니터링
- **데이터 소스 설정**: Jira/Confluence 연결 설정 관리

## 기술 스택

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL (SQLite for dev)
- **ORM**: SQLAlchemy 2.0
- **Settings**: pydantic-settings

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: Zustand
- **Data Fetching**: TanStack React Query
- **Charts**: Recharts

### AI/ML
- **LLM**: OpenAI GPT-4o-mini / Azure OpenAI GPT-4o
- **Embeddings**: text-embedding-3-large (3072 dimensions)
- **Vector DB**: FAISS IndexFlatL2
- **Framework**: LangChain, LangGraph

### External APIs
- **Atlassian**: atlassian-python-api (Jira, Confluence)

## 스크린샷

### Landing Page
사용자 친화적인 랜딩 페이지로 주요 기능 소개

### Chat Interface
RAG 기반 AI 챗봇 인터페이스 (출처 카드 포함)

### Dashboard
동기화 상태, 문서 통계, 활동 로그 모니터링

### Settings
Jira/Confluence 연결 설정 및 동기화 규칙 관리

## LangGraph Workflow

사용자 질문에 대해 RAG 기반 답변을 생성하는 LangGraph 워크플로우입니다.

![LangGraph Workflow](docs/workflow_diagram.png)

### 워크플로우 단계

| 단계 | Agent | 설명 |
|------|-------|------|
| 1 | **Query Analyzer** | 사용자 쿼리 분석 (intent, keywords, filters 추출) |
| 2 | **RAG Searcher** | FAISS 벡터 DB에서 유사 문서 검색 (Top-5) |
| 3 | **Relevance Checker** | 검색 결과 관련성 평가 (threshold + LLM 검증) |
| 4a | **RAG Responder** | 관련 문서 기반 응답 생성 (출처 포함) |
| 4b | **LLM Fallback** | 관련 문서 없을 시 일반 지식 기반 응답 |
| 5 | **Response Formatter** | 최종 응답 마크다운 포맷팅 |

### 응답 유형

- **RAG 응답**: 회사 문서(Jira/Confluence) 기반 답변 + 출처 링크
- **Fallback 응답**: 일반 LLM 지식 기반 답변 + 면책 문구

## 프로젝트 구조

```
knowledge-base-ai-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI 앱 엔트리포인트
│   │   ├── config.py                   # 환경 설정
│   │   ├── database.py                 # DB 연결
│   │   ├── state.py                    # 앱 상태 관리
│   │   ├── api/                        # API 라우터
│   │   │   ├── chat.py                 # 채팅 API
│   │   │   ├── dashboard.py            # 대시보드 API
│   │   │   ├── feedback.py             # 피드백 API
│   │   │   ├── health.py               # 헬스체크 API
│   │   │   ├── settings.py             # 설정 API
│   │   │   └── stats.py                # 통계 API
│   │   ├── models/                     # SQLAlchemy 모델
│   │   │   ├── document.py             # 문서, 청크
│   │   │   ├── chat.py                 # 채팅 이력
│   │   │   ├── feedback.py             # 피드백
│   │   │   └── sync.py                 # 동기화 이력
│   │   ├── schemas/                    # Pydantic 스키마
│   │   │   ├── chat.py                 # 채팅 요청/응답
│   │   │   ├── dashboard.py            # 대시보드 스키마
│   │   │   └── settings.py             # 설정 스키마
│   │   ├── utils/                      # 유틸리티
│   │   │   ├── text_splitter.py        # 텍스트 청킹
│   │   │   └── storage.py              # Cloud Storage
│   │   └── core/
│   │       ├── services/               # 비즈니스 로직
│   │       │   ├── jira_client.py      # Jira API
│   │       │   ├── confluence_client.py # Confluence API
│   │       │   ├── data_collector.py   # 데이터 수집
│   │       │   ├── embedding_service.py # OpenAI 임베딩
│   │       │   ├── vector_db_service.py # FAISS 벡터 DB
│   │       │   ├── rag_service.py      # RAG 검색
│   │       │   └── llm_service.py      # LLM 서비스
│   │       ├── agents/                 # LangGraph 에이전트
│   │       │   ├── query_analyzer.py   # 쿼리 분석
│   │       │   ├── rag_searcher.py     # RAG 검색
│   │       │   ├── relevance_checker.py # 관련성 평가
│   │       │   ├── rag_responder.py    # RAG 응답
│   │       │   ├── llm_fallback.py     # LLM 폴백
│   │       │   └── response_formatter.py # 응답 포맷팅
│   │       └── workflow/               # LangGraph 워크플로우
│   │           ├── state.py            # ChatState 정의
│   │           └── graph.py            # 워크플로우 그래프
│   ├── scripts/
│   │   ├── init_db.py                  # DB 초기화
│   │   ├── collect_data.py             # 데이터 수집 CLI
│   │   ├── build_vector_db.py          # 벡터 DB 빌드
│   │   ├── test_search.py              # 검색 테스트
│   │   └── test_workflow.py            # 워크플로우 테스트
│   ├── data/
│   │   ├── database/                   # SQLite DB (dev)
│   │   └── vector_db/                  # FAISS 인덱스
│   ├── requirements.txt
│   └── .env                            # (gitignore)
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                     # 앱 엔트리포인트
│   │   ├── main.tsx                    # React 렌더링
│   │   ├── components/
│   │   │   ├── layout/                 # 레이아웃 컴포넌트
│   │   │   │   ├── Layout.tsx          # 메인 레이아웃
│   │   │   │   ├── Header.tsx          # 헤더
│   │   │   │   ├── Footer.tsx          # 푸터
│   │   │   │   └── AdminLayout.tsx     # 관리자 레이아웃
│   │   │   ├── landing/                # 랜딩 페이지
│   │   │   │   └── LandingPage.tsx     # 랜딩 페이지
│   │   │   ├── chat/                   # 채팅 컴포넌트
│   │   │   │   ├── ChatContainer.tsx   # 채팅 컨테이너
│   │   │   │   ├── MessageList.tsx     # 메시지 목록
│   │   │   │   ├── ChatInput.tsx       # 입력창
│   │   │   │   └── SourceCard.tsx      # 출처 카드
│   │   │   ├── dashboard/              # 대시보드 컴포넌트
│   │   │   │   ├── StatCard.tsx        # 통계 카드
│   │   │   │   ├── AlertBanner.tsx     # 알림 배너
│   │   │   │   ├── DataSourceCard.tsx  # 데이터 소스 카드
│   │   │   │   ├── SyncChart.tsx       # 동기화 차트
│   │   │   │   ├── SyncActivityTable.tsx # 활동 테이블
│   │   │   │   └── DashboardHeader.tsx # 대시보드 헤더
│   │   │   ├── settings/               # 설정 컴포넌트
│   │   │   │   ├── ConnectionStatus.tsx # 연결 상태
│   │   │   │   ├── ConnectionSettings.tsx # 연결 설정
│   │   │   │   ├── SyncRules.tsx       # 동기화 규칙
│   │   │   │   └── DataSourceTabs.tsx  # 데이터 소스 탭
│   │   │   └── ui/                     # shadcn/ui 컴포넌트
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx       # 대시보드 페이지
│   │   │   └── SettingsPage.tsx        # 설정 페이지
│   │   ├── hooks/
│   │   │   ├── useDashboard.ts         # 대시보드 훅
│   │   │   └── useSettings.ts          # 설정 훅
│   │   ├── store/
│   │   │   └── chatStore.ts            # Zustand 스토어
│   │   ├── services/
│   │   │   └── api.ts                  # API 클라이언트
│   │   └── lib/
│   │       └── utils.ts                # 유틸리티
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
│
└── docs/
    ├── workflow_diagram.png            # 워크플로우 다이어그램
    ├── knowledge-base-ai-chatbot-plan.md
    └── knowledge-base-ai-chatbot-todo.md
```

## API 엔드포인트

### Chat API
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | 채팅 메시지 전송 및 AI 응답 |
| GET | `/api/chat/history` | 채팅 이력 조회 |

### Dashboard API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | 대시보드 통계 |
| GET | `/api/dashboard/sync-history` | 동기화 이력 |
| POST | `/api/dashboard/sync` | 수동 동기화 트리거 |

### Settings API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings/data-sources` | 데이터 소스 설정 조회 |
| PUT | `/api/settings/data-sources/{source}` | 데이터 소스 설정 저장 |
| POST | `/api/settings/test-connection` | 연결 테스트 |

### Other APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | 헬스체크 |
| GET | `/api/stats` | 시스템 통계 |
| POST | `/api/feedback` | 피드백 제출 |

## 설치 및 실행

### 1. Backend 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 API 키 설정
```

### 2. PostgreSQL 데이터베이스 설정

```bash
# 데이터베이스 생성
createdb knowledge_base

# 테이블 생성
python scripts/init_db.py
```

### 3. Jira/Confluence 설정

`.env` 파일에 Atlassian 인증 정보 설정:

```env
# Jira 설정
JIRA_URL=http://localhost:8080
JIRA_USERNAME=admin
JIRA_API_TOKEN=your_personal_access_token
JIRA_PROJECT_KEY=TEST

# Confluence 설정
CONFLUENCE_URL=http://localhost:8090
CONFLUENCE_USERNAME=admin
CONFLUENCE_API_TOKEN=your_personal_access_token
CONFLUENCE_SPACE_KEY=TES

# OpenAI 설정
OPENAI_API_KEY=your_openai_api_key
```

### 4. 데이터 수집 및 벡터 DB 빌드

```bash
# 전체 수집
python scripts/collect_data.py --source all

# 벡터 DB 빌드
python scripts/build_vector_db.py

# 워크플로우 테스트
python scripts/test_workflow.py --query "API 사용법을 알려주세요"
```

### 5. Backend 서버 실행

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 6. Frontend 설정 및 실행

```bash
cd frontend

# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env
# VITE_API_URL=http://localhost:8000 설정

# 개발 서버 실행
npm run dev
```

Frontend: http://localhost:5173
Backend API: http://localhost:8000/docs

## 인증 방식

### Personal Access Token (PAT) - 권장

로컬 서버에서 Basic Auth가 비활성화된 경우 PAT 사용:

1. Jira/Confluence 프로필 설정으로 이동
2. Personal Access Tokens 메뉴에서 토큰 생성
3. `.env` 파일의 `*_API_TOKEN`에 설정

### Basic Auth

Cloud 환경 또는 Basic Auth가 활성화된 경우:

```env
JIRA_USERNAME=your_email
JIRA_PASSWORD=your_api_token  # Cloud의 경우 API 토큰
```

## 데이터베이스 스키마

### documents
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| doc_id | String | 고유 문서 ID (jira-XXX, confluence-XXX) |
| doc_type | String | jira / confluence |
| title | String | 제목 |
| content | Text | 본문 |
| url | String | 원본 URL |
| is_deleted | Boolean | 삭제 여부 (soft delete) |

### document_chunks
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| document_id | Integer | FK → documents.id |
| chunk_index | Integer | 청크 인덱스 |
| content | Text | 청크 내용 |
| embedding | JSON | 임베딩 벡터 (3072 dim) |

### sync_history
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| sync_type | String | jira / confluence / all |
| status | String | running / completed / failed |
| documents_added | Integer | 추가된 문서 수 |
| documents_updated | Integer | 업데이트된 문서 수 |
| documents_deleted | Integer | 삭제된 문서 수 |

## 개발 로드맵

- [x] Week 1: 프로젝트 초기 설정 및 데이터 수집
- [x] Week 2: 임베딩 및 벡터 DB 구축 (FAISS, text-embedding-3-large)
- [x] Week 3: LangGraph 워크플로우 및 RAG 파이프라인
- [x] Week 4: FastAPI 엔드포인트 구현 (Chat, Health, Stats, Feedback)
- [x] Week 5: 배치 프로세스 (증분 동기화)
- [x] Week 6: React 프론트엔드 - Landing Page & Chat Interface
- [x] Week 7: React 프론트엔드 - Dashboard & Settings 페이지
- [ ] Week 8: GCP 배포 (Cloud Run, Cloud SQL)
- [ ] Week 9-10: 테스트, 최적화, 문서화

## 라이선스

Private - 내부 사용 전용
