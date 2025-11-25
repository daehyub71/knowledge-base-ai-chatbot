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

## 기술 스택

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0
- **Settings**: pydantic-settings

### AI/ML (예정)
- **LLM**: Azure OpenAI (GPT-4o) / OpenAI / Anthropic Claude
- **Embeddings**: text-embedding-3-large
- **Vector DB**: FAISS
- **Framework**: LangChain, LangGraph

### External APIs
- **Atlassian**: atlassian-python-api (Jira, Confluence)

## 프로젝트 구조

```
knowledge-base-ai-chatbot/
├── backend/
│   ├── app/
│   │   ├── config.py              # 환경 설정
│   │   ├── database.py            # DB 연결
│   │   ├── models/                # SQLAlchemy 모델
│   │   │   ├── document.py        # 문서, 청크
│   │   │   ├── chat.py            # 채팅 이력
│   │   │   ├── feedback.py        # 피드백
│   │   │   └── sync.py            # 동기화 이력
│   │   └── core/
│   │       └── services/          # 비즈니스 로직
│   │           ├── jira_client.py
│   │           ├── confluence_client.py
│   │           ├── data_collector.py
│   │           ├── incremental_sync.py
│   │           └── deletion_detector.py
│   ├── scripts/
│   │   ├── init_db.py             # DB 초기화
│   │   ├── collect_data.py        # 데이터 수집 CLI
│   │   ├── test_jira.py           # Jira 테스트
│   │   └── test_confluence.py     # Confluence 테스트
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                       # (gitignore)
└── docs/
    ├── knowledge-base-ai-chatbot-plan.md
    └── knowledge-base-ai-chatbot-todo.md
```

## 설치 및 실행

### 1. 환경 설정

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
```

### 4. 데이터 수집

```bash
# 전체 수집
python scripts/collect_data.py --source all

# Jira만 수집
python scripts/collect_data.py --source jira

# Confluence만 수집
python scripts/collect_data.py --source confluence

# 삭제된 문서 감지
python scripts/collect_data.py --source all --detect-deleted

# 전체 재동기화
python scripts/collect_data.py --source all --full-sync
```

### 5. 연결 테스트

```bash
# Jira 연결 테스트
python scripts/test_jira.py

# Confluence 연결 테스트
python scripts/test_confluence.py
```

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

### sync_history
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| source_type | String | jira / confluence / all |
| status | String | started / completed / failed |
| documents_added | Integer | 추가된 문서 수 |
| documents_updated | Integer | 업데이트된 문서 수 |
| documents_deleted | Integer | 삭제된 문서 수 |

## 개발 로드맵

- [x] Week 1: 프로젝트 초기 설정 및 데이터 수집
- [ ] Week 2: 임베딩 및 벡터 DB 구축
- [ ] Week 3: RAG 파이프라인 및 LLM 연동
- [ ] Week 4: API 엔드포인트 및 프론트엔드

## 라이선스

Private - 내부 사용 전용
