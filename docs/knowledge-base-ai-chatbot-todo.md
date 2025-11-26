# Knowledge Base AI Chatbot - 상세 작업 목록 (TODO List)

**프로젝트 위치**: `/Users/sunchulkim/src/knowledge-base-ai-chatbot/`
**작성일**: 2025-01-24

---

## 📋 Week 1: 프로젝트 초기 설정 및 데이터 수집

### 프로젝트 구조 생성
- [x] 프로젝트 루트 디렉토리 생성 (`knowledge-base-ai-chatbot/`)
- [x] `backend/` 디렉토리 구조 생성
  - [x] `app/`, `batch/`, `tests/`, `scripts/` 디렉토리
  - [x] `app/` 하위: `models/`, `schemas/`, `api/`, `core/`, `utils/`
  - [x] `core/` 하위: `agents/`, `workflow/`, `services/`
- [x] `frontend/` 디렉토리 구조 생성 (Week 6에서 완료)
- [x] Git 저장소 초기화 (`git init`)
- [x] `.gitignore` 파일 작성

### Python 환경 설정
- [x] `backend/` 디렉토리에 가상환경 생성 (`python3 -m venv venv`)
- [x] 가상환경 활성화
- [x] `requirements.txt` 작성
  - [x] fastapi, uvicorn
  - [x] sqlalchemy, psycopg2-binary
  - [x] langchain, langgraph, langchain-openai
  - [x] faiss-cpu
  - [x] google-cloud-storage
  - [x] atlassian-python-api
  - [x] python-dotenv
  - [x] pydantic, pydantic-settings
- [x] 의존성 패키지 설치 (`pip install -r requirements.txt`)

### 환경 변수 설정
- [x] `backend/.env.example` 파일 작성 (12장 참고)
- [x] `backend/.env` 파일 생성 (실제 값 입력)
  - [x] DATABASE_URL (로컬 PostgreSQL)
  - [x] AZURE_OPENAI_API_KEY, ENDPOINT, DEPLOYMENT
  - [x] OPENAI_API_KEY (또는 ANTHROPIC_API_KEY)
  - [x] JIRA_URL, USERNAME, API_TOKEN, PROJECT_KEY (로컬 서버용)
  - [x] CONFLUENCE_URL, USERNAME, PASSWORD, API_TOKEN, SPACE_KEY (로컬 서버용)
  - [x] MCP_BASE_URL, MCP_JIRA_URL, MCP_CONFLUENCE_URL
  - [ ] GCS_BUCKET_NAME (나중에 설정)

### PostgreSQL 설정
- [x] 로컬 PostgreSQL 설치 확인 (`brew services list`)
- [x] 데이터베이스 생성 (`createdb knowledge_base`)
- [x] `backend/app/database.py` 작성
  - [x] SQLAlchemy 엔진 생성
  - [x] SessionLocal 설정
  - [x] Base 선언
- [x] `backend/app/config.py` 작성
  - [x] pydantic-settings로 환경변수 로드
  - [x] Settings 클래스 정의
  - [x] 로컬 Jira/Confluence 서버 지원 추가 (username, password, project_key, space_key)

### 데이터베이스 모델 생성 (SQLAlchemy)
- [x] `backend/app/models/document.py` 작성
  - [x] `Document` 모델 (id, doc_id, doc_type, title, url, content, author, created_at, updated_at, last_synced_at, deleted, metadata)
  - [x] `DocumentChunk` 모델 (id, document_id, chunk_index, chunk_text, faiss_index_id, created_at)
- [x] `backend/app/models/chat.py` 작성
  - [x] `ChatHistory` 모델 (id, session_id, user_query, response, response_type, source_documents, relevance_score, created_at)
- [x] `backend/app/models/feedback.py` 작성
  - [x] `Feedback` 모델 (id, chat_history_id, rating, comment, created_at)
- [x] `backend/app/models/sync.py` 작성
  - [x] `SyncHistory` 모델 (id, sync_type, status, documents_added, documents_updated, documents_deleted, error_message, started_at, completed_at)

### 데이터베이스 초기화 스크립트
- [x] `backend/scripts/init_db.py` 작성
  - [x] `Base.metadata.create_all()` 실행
  - [x] 테이블 생성 확인 쿼리
- [x] 스크립트 실행하여 테이블 생성 확인

### Jira API 클라이언트 구현
- [x] `backend/app/core/services/jira_client.py` 작성
  - [x] `JiraClient` 클래스 생성
  - [x] `__init__`: atlassian-python-api의 Jira 초기화
  - [x] 로컬 서버/Cloud 자동 감지 (cloud 파라미터)
  - [x] username/email 모두 지원
  - [x] default_project_key 지원
  - [x] `get_all_projects()`: 모든 프로젝트 조회
  - [x] `get_issues_updated_since(last_sync)`: JQL로 증분 조회
  - [x] `get_issue_details(issue_key)`: 이슈 상세 정보 (description, comments)
  - [x] `get_comments(issue_key)`: 주석 가져오기
- [x] Jira 연결 테스트 스크립트 작성 (`scripts/test_jira.py`)
- [ ] 실제 Jira에서 샘플 이슈 5개 가져오기 테스트

### Confluence API 클라이언트 구현
- [x] `backend/app/core/services/confluence_client.py` 작성
  - [x] `ConfluenceClient` 클래스 생성
  - [x] `__init__`: atlassian-python-api의 Confluence 초기화
  - [x] 로컬 서버/Cloud 자동 감지 (cloud 파라미터)
  - [x] username/email, password/api_token 모두 지원
  - [x] default_space_key 지원
  - [x] `get_all_spaces()`: 모든 Space 조회
  - [x] `get_pages_updated_since(last_sync)`: CQL로 증분 조회
  - [x] `get_page_content(page_id)`: 페이지 본문 가져오기
  - [x] `get_page_comments(page_id)`: 주석 가져오기
- [x] Confluence 연결 테스트 스크립트 작성 (`scripts/test_confluence.py`)
- [ ] 실제 Confluence에서 샘플 페이지 5개 가져오기 테스트

### 데이터 수집 로직 구현
- [x] `backend/app/core/services/data_collector.py` 작성
  - [x] `collect_jira_documents()` 함수
    - [x] Jira 이슈 조회
    - [x] PostgreSQL에 저장 (Document 테이블)
    - [x] 중복 체크 (doc_id 기준)
  - [x] `collect_confluence_documents()` 함수
    - [x] Confluence 페이지 조회
    - [x] PostgreSQL에 저장
    - [x] 중복 체크
- [x] `backend/scripts/collect_data.py` 작성
  - [x] argparse로 `--source jira/confluence` 옵션
  - [x] 전체 수집 실행
  - [x] 수집 결과 통계 출력
- [x] 스크립트 실행하여 실제 데이터 수집
  - [x] `python scripts/collect_data.py --source jira` (0개 이슈)
  - [x] `python scripts/collect_data.py --source confluence` (9개 페이지)
  - [x] PostgreSQL에서 데이터 확인 (`SELECT COUNT(*) FROM documents;`)

### 증분 업데이트 로직 구현
- [x] `backend/app/core/services/incremental_sync.py` 작성
  - [x] `get_last_sync_time(source)` 함수
    - [x] sync_history 테이블에서 마지막 성공 시간 조회
  - [x] `fetch_incremental_jira(last_sync)` 함수
    - [x] `updated >= last_sync` JQL 쿼리
    - [x] 변경된 이슈만 가져오기
  - [x] `fetch_incremental_confluence(last_sync)` 함수
    - [x] `lastModified >= last_sync` CQL 쿼리
    - [x] 변경된 페이지만 가져오기
- [ ] 증분 업데이트 테스트
  - [ ] 기존 문서 수정 후 재수집 확인

### 삭제된 문서 감지 로직 구현
- [x] `backend/app/core/services/deletion_detector.py` 작성
  - [x] `detect_deleted_documents(source, current_doc_ids)` 함수
    - [x] PostgreSQL의 doc_id 집합 조회
    - [x] Jira/Confluence의 현재 doc_id 집합과 비교
    - [x] 차집합 → deleted=True 업데이트
- [ ] 삭제 감지 테스트
  - [ ] 테스트 이슈/페이지 삭제 후 감지 확인

### Week 1 마무리
- [ ] 코드 리뷰 및 리팩토링
- [ ] 유닛 테스트 작성 (JiraClient, ConfluenceClient)
- [ ] README.md 초안 작성 (프로젝트 소개, 설치 방법)
- [ ] Git 커밋 (`Week 1 완료: 데이터 수집 시스템`)

---

## 📋 Week 2: RAG 시스템 구축

### 텍스트 청킹 구현
- [x] `backend/app/utils/text_splitter.py` 작성
  - [x] `chunk_documents(documents)` 함수
    - [x] RecursiveCharacterTextSplitter 사용
    - [x] chunk_size=1000, chunk_overlap=200
    - [x] 청크 목록 반환 (텍스트 + 메타데이터)
- [x] 청킹 테스트
  - [x] 샘플 문서로 청킹 실행
  - [x] 청크 개수, 크기 확인

### OpenAI 임베딩 서비스 구현
- [x] `backend/app/core/services/embedding_service.py` 작성
  - [x] `EmbeddingService` 클래스 생성
  - [x] `__init__`: OpenAI 클라이언트 초기화
  - [x] `get_embedding(text)` 함수
    - [x] text-embedding-3-large 호출
    - [x] 벡터 반환 (3072차원)
  - [x] `get_embeddings_batch(texts)` 함수
    - [x] 배치 처리 (100개씩)
    - [x] 벡터 리스트 반환
- [x] 임베딩 테스트
  - [x] 샘플 텍스트 5개로 임베딩 생성
  - [x] 벡터 차원 확인 (3072차원)

### FAISS 인덱스 빌드 로직 구현
- [x] `backend/app/core/services/vector_db_service.py` 작성
  - [x] `VectorDBService` 클래스 생성
  - [x] `create_index(dimension)` 함수
    - [x] FAISS IndexFlatL2 생성
  - [x] `add_vectors(vectors, metadata)` 함수
    - [x] 인덱스에 벡터 추가
    - [x] metadata.pkl에 메타데이터 저장
  - [x] `search(query_vector, k=5)` 함수
    - [x] 유사도 검색
    - [x] (index_id, score) 리스트 반환
  - [x] `save_index(filepath)` 함수
    - [x] FAISS 인덱스 저장
  - [x] `load_index(filepath)` 함수
    - [x] FAISS 인덱스 로드
- [x] FAISS 인덱스 테스트
  - [x] 샘플 벡터 10개로 인덱스 생성
  - [x] 검색 테스트

### Cloud Storage 통합
- [ ] GCP 프로젝트 생성 (콘솔에서)
- [ ] Cloud Storage 버킷 생성
  - [ ] 버킷 이름: `knowledge-base-{PROJECT_ID}`
  - [ ] 리전: `asia-northeast3` (서울)
- [ ] 서비스 계정 생성 및 키 다운로드
  - [ ] IAM > 서비스 계정 > 키 생성 (JSON)
  - [ ] `backend/service-account.json` 저장 (gitignore 추가)
- [x] `backend/app/utils/storage.py` 작성
  - [x] `StorageClient` 클래스 생성
  - [x] `__init__`: google-cloud-storage 클라이언트 초기화
  - [x] `upload_file(local_path, gcs_path)` 함수
  - [x] `download_file(gcs_path, local_path)` 함수
  - [x] `file_exists(gcs_path)` 함수
- [ ] Cloud Storage 테스트 (GCP 설정 후 진행)
  - [ ] 샘플 파일 업로드
  - [ ] 다운로드 후 내용 확인

### 벡터 DB 빌드 스크립트 작성
- [x] `backend/scripts/build_vector_db.py` 작성
  - [x] PostgreSQL에서 모든 문서 조회
  - [x] 텍스트 청킹 (DocumentChunk 테이블에 저장)
  - [x] 각 청크에 대해 임베딩 생성
  - [x] FAISS 인덱스에 추가
  - [x] faiss_index_id 매핑 저장 (DocumentChunk 테이블)
  - [x] FAISS 인덱스 저장 (로컬)
  - [ ] Cloud Storage에 업로드 (Week 8 배포 시 진행)
  - [x] 진행 상황 로깅
- [x] 스크립트 실행
  - [x] `python scripts/build_vector_db.py`
  - [x] 실행 시간: 2.14초 (9개 문서, 9개 청크)
  - [x] FAISS 인덱스 파일 생성 확인 (`data/vector_db/faiss.index`)

### 벡터 검색 함수 구현
- [x] `backend/app/core/services/rag_service.py` 작성
  - [x] `RAGService` 클래스 생성
  - [x] `__init__`: VectorDBService, EmbeddingService 초기화
  - [x] `search_documents(query, top_k=5)` 함수
    - [x] 쿼리 임베딩 생성
    - [x] FAISS 검색
    - [x] PostgreSQL에서 메타데이터 조회
    - [x] 결과 반환 (doc_id, title, content, score, url, author, updated_at)

### 메타데이터 필터링 구현
- [x] `RAGService.search_documents()`에 필터링 추가
  - [x] `deleted=False` 문서만 반환
  - [x] 옵션: doc_type 필터 (jira/confluence)
  - [x] 옵션: 날짜 범위 필터

### 검색 품질 테스트
- [x] `backend/scripts/test_search.py` 작성
  - [x] 10개 샘플 쿼리 준비
  - [x] 각 쿼리에 대해 검색 실행
  - [x] Top-5 결과 출력
  - [x] 유사도 점수 확인
- [x] 검색 품질 평가
  - [x] 관련 문서가 상위 결과에 나오는지 확인 (정상 동작)
  - [x] 임계값 조정: 0.7 → 0.3~0.4 권장 (현재 데이터 기준)

### Week 2 마무리
- [ ] 코드 리뷰 및 리팩토링
- [ ] 유닛 테스트 작성 (EmbeddingService, VectorDBService, RAGService)
- [ ] FAISS 인덱스 백업 (Cloud Storage)
- [ ] Git 커밋 (`Week 2 완료: RAG 시스템 구축`)

---

## 📋 Week 3: LangGraph 워크플로우 구현

### LangGraph State 정의
- [x] `backend/app/core/workflow/state.py` 작성
  - [x] `ChatState` TypedDict 정의
    - [x] user_query: str
    - [x] analyzed_query: dict
    - [x] search_results: List[dict]
    - [x] relevance_decision: Literal["relevant", "irrelevant"]
    - [x] response: str
    - [x] response_type: Literal["rag", "llm_fallback"]
    - [x] sources: List[dict]

### OpenAI LLM 서비스 구현
- [x] `backend/app/core/services/llm_service.py` 작성
  - [x] `LLMService` 클래스 생성
  - [x] `__init__`: OpenAI 클라이언트 초기화 (gpt-4o-mini, gpt-4o 선택 가능)
  - [x] `generate(prompt, system_message=None)` 함수
    - [x] ChatCompletion API 호출
    - [x] 응답 텍스트 반환
  - [x] `generate_json(prompt)` 함수 → `analyze_query()` 로 구현
    - [x] JSON 형식 응답 강제
    - [x] 파싱하여 dict 반환

### Agent 1: QueryAnalyzer
- [x] `backend/app/core/agents/query_analyzer.py` 작성
  - [x] `query_analyzer(state: ChatState) -> ChatState` 함수
  - [x] 프롬프트 작성
    - [x] 사용자 문의 분석 요청
    - [x] intent, keywords, entities 추출
    - [x] JSON 형식으로 반환
  - [x] LLMService.analyze_query() 호출
  - [x] state["analyzed_query"] 업데이트
- [x] 단위 테스트 작성
  - [x] 샘플 쿼리 5개로 테스트
  - [x] 출력 형식 검증

### Agent 2: RAGSearcher
- [x] `backend/app/core/agents/rag_searcher.py` 작성
  - [x] `rag_searcher(state: ChatState) -> ChatState` 함수
  - [x] RAGService.search_documents() 호출
  - [x] Top-K 결과 가져오기 (K=5)
  - [x] state["search_results"] 업데이트
- [x] 단위 테스트 작성
  - [x] 샘플 쿼리로 검색 실행
  - [x] 결과 개수 확인

### Agent 3: RelevanceChecker
- [x] `backend/app/core/agents/relevance_checker.py` 작성
  - [x] `relevance_checker(state: ChatState) -> ChatState` 함수
  - [x] 단계 1: 유사도 점수 임계값 체크 (0.35로 조정)
    - [x] 최고 점수가 임계값 미만이면 "irrelevant"
  - [x] 단계 2: LLM으로 관련성 재확인
    - [x] 프롬프트: "이 문서가 질문에 답변할 수 있나요?"
    - [x] yes/no 응답
  - [x] state["relevance_decision"] 업데이트
- [x] 단위 테스트 작성
  - [x] 관련 있는 케이스, 없는 케이스 각각 테스트

### Agent 4a: RAGResponder
- [x] `backend/app/core/agents/rag_responder.py` 작성
  - [x] `rag_responder(state: ChatState) -> ChatState` 함수
  - [x] 프롬프트 작성
    - [x] 검색된 문서 컨텍스트 포함 (Top-3)
    - [x] 사용자 질문에 답변 요청
  - [x] LLMService.generate_with_context() 호출
  - [x] state["response"] 업데이트
  - [x] state["response_type"] = "rag"
  - [x] state["sources"] = 검색 결과
- [x] 단위 테스트 작성
  - [x] 샘플 검색 결과로 답변 생성

### Agent 4b: LLMFallback
- [x] `backend/app/core/agents/llm_fallback.py` 작성
  - [x] `llm_fallback(state: ChatState) -> ChatState` 함수
  - [x] 프롬프트 작성
    - [x] "회사 문서에 없는 내용입니다"
    - [x] 일반 지식으로 답변
    - [x] 답변 끝에 면책 문구 추가
  - [x] LLMService.generate() 호출
  - [x] state["response"] 업데이트
  - [x] state["response_type"] = "llm_fallback"
  - [x] state["sources"] = []
- [x] 단위 테스트 작성
  - [x] 관련 문서 없는 쿼리로 답변 생성

### Agent 5: ResponseFormatter
- [x] `backend/app/core/agents/response_formatter.py` 작성
  - [x] `response_formatter(state: ChatState) -> ChatState` 함수
  - [x] Markdown 형식으로 포맷팅
    - [x] 답변 본문
    - [x] "### 📚 참고 문서" 섹션
    - [x] 각 문서: [제목](URL), doc_type 표시
  - [x] state["response"] 업데이트
- [x] 단위 테스트 작성
  - [x] 출력 형식 검증

### LangGraph 워크플로우 그래프 구성
- [x] `backend/app/core/workflow/graph.py` 작성
  - [x] StateGraph(ChatState) 생성
  - [x] 6개 노드 추가 (query_analyzer, rag_searcher, relevance_checker, rag_responder, llm_fallback, response_formatter)
  - [x] 엣지 연결
    - [x] entry_point → query_analyzer
    - [x] query_analyzer → rag_searcher
    - [x] rag_searcher → relevance_checker
    - [x] relevance_checker → (조건부) rag_responder or llm_fallback
    - [x] rag_responder → response_formatter
    - [x] llm_fallback → response_formatter
    - [x] response_formatter → END
  - [x] 워크플로우 컴파일 (`app = workflow.compile()`)
  - [x] `run_workflow(user_query)` 함수 작성

### End-to-End 테스트
- [x] `backend/scripts/test_workflow.py` 작성
  - [x] 10개 샘플 쿼리 준비
    - [x] 5개: RAG에서 답변 가능한 질문
    - [x] 5개: 일반 지식 질문
  - [x] 각 쿼리에 대해 워크플로우 실행
  - [x] 응답 타입 (rag/llm_fallback) 확인
  - [x] 답변 품질 수동 검증
- [x] 스크립트 실행 및 결과 분석

### 워크플로우 시각화
- [x] LangGraph 그래프 시각화 코드 작성
  - [x] `app.get_graph().draw_mermaid_png()` 사용
  - [x] 이미지 파일 저장 (`docs/workflow_diagram.png`)
  - [x] Mermaid 마크다운 문서 (`docs/workflow_diagram.md`)

### Week 3 마무리
- [x] 코드 리뷰 및 리팩토링
- [x] 유닛 테스트 작성 (각 에이전트) - test_workflow.py에 통합
- [x] 통합 테스트 작성 (전체 워크플로우) - test_workflow.py
- [x] Git 커밋 (`Week 3 완료: LangGraph 워크플로우`)

---

## 📋 Week 4: API 엔드포인트 구현

### FastAPI 앱 초기화
- [x] `backend/app/main.py` 작성
  - [x] FastAPI() 인스턴스 생성
  - [x] CORS 설정 (CORSMiddleware)
  - [x] 라우터 등록 준비
  - [x] 시작/종료 이벤트 핸들러
    - [x] startup: FAISS 인덱스 로드
    - [x] shutdown: DB 연결 종료

### Pydantic 스키마 정의
- [x] `backend/app/schemas/chat.py` 작성
  - [x] `ChatRequest` (query, session_id)
  - [x] `Source` (doc_id, doc_type, title, url, score, snippet)
  - [x] `ChatResponse` (response, response_type, sources, relevance_decision, analyzed_query, session_id, error)
- [x] `backend/app/schemas/feedback.py` 작성
  - [x] `FeedbackRequest` (session_id, message_id, rating, comment, feedback_type)
  - [x] `FeedbackResponse` (success, feedback_id, message, created_at)
- [x] `backend/app/schemas/stats.py` 작성
  - [x] `DocumentStats` (total_documents, jira_documents, confluence_documents, active_documents, deleted_documents, total_chunks, vector_count)
  - [x] `SyncStats` (last_sync_at, last_sync_status, documents_added, documents_updated, documents_deleted)
  - [x] `ChatStats` (total_sessions, total_messages, rag_responses, fallback_responses, positive_feedback, negative_feedback)
  - [x] `StatsResponse` (documents, sync, chat, status, updated_at)

### API 엔드포인트 1: POST /api/chat
- [x] `backend/app/api/chat.py` 작성
  - [x] `@app.post("/api/chat")` 엔드포인트
  - [x] ChatRequest 받기
  - [x] 워크플로우 실행 (`run_workflow(query)`)
  - [x] ChatHistory 테이블에 저장
    - [x] session_id, user_query, response, response_type, source_documents, relevance_score
  - [x] ChatResponse 반환
- [x] 단위 테스트 작성
  - [x] pytest로 API 호출 테스트
  - [x] 응답 형식 검증

### API 엔드포인트 2: POST /api/feedback
- [x] `backend/app/api/feedback.py` 작성
  - [x] `@app.post("/api/feedback")` 엔드포인트
  - [x] FeedbackRequest 받기
  - [x] Feedback 테이블에 저장
    - [x] chat_history_id, rating, comment
  - [x] FeedbackResponse 반환
- [x] 단위 테스트 작성

### API 엔드포인트 3: GET /api/health
- [x] `backend/app/api/health.py` 작성
  - [x] `@app.get("/api/health")` 엔드포인트
  - [x] 데이터베이스 연결 확인 (simple query)
  - [x] FAISS 인덱스 로드 상태 확인
  - [x] sync_history에서 마지막 동기화 시간 조회
  - [x] HealthResponse 반환
- [x] 단위 테스트 작성

### API 엔드포인트 4: GET /api/stats
- [x] `backend/app/api/stats.py` 작성
  - [x] `@app.get("/api/stats")` 엔드포인트
  - [x] PostgreSQL에서 통계 집계
    - [x] `SELECT COUNT(*) FROM documents`
    - [x] `SELECT COUNT(*) FROM document_chunks`
    - [x] Jira 문서 수, Confluence 문서 수
    - [x] 오늘 채팅 수 (`created_at >= today`)
    - [x] RAG 응답 비율 (`response_type='rag'`)
    - [x] 평균 피드백 (`AVG(rating)`)
  - [x] StatsResponse 반환
- [x] 단위 테스트 작성

### 라우터 등록
- [x] `backend/app/main.py`에 라우터 등록
  - [x] `app.include_router(chat_router, prefix="/api")`
  - [x] `app.include_router(feedback_router, prefix="/api")`
  - [x] `app.include_router(health_router, prefix="/api")`
  - [x] `app.include_router(stats_router, prefix="/api")`
- [x] `backend/app/state.py` 작성 (순환 참조 해결용)
  - [x] VectorDBService 전역 상태 관리
  - [x] get_vector_db_service(), set_vector_db_service() 함수

### 에러 핸들링
- [x] `backend/app/utils/exceptions.py` 작성
  - [x] 커스텀 예외 클래스 (KnowledgeBaseException, DocumentNotFoundError, ChatHistoryNotFoundError, etc.)
- [x] `backend/app/main.py`에 예외 핸들러 등록
  - [x] `@app.exception_handler(KnowledgeBaseException)`
  - [x] `@app.exception_handler(Exception)`
  - [x] JSON 형식 에러 응답

### 로깅 설정
- [x] `backend/app/utils/logger.py` 작성
  - [x] Python logging 설정
  - [x] 파일 핸들러 (logs/app.log) - RotatingFileHandler
  - [x] 콘솔 핸들러
  - [x] 로그 레벨 (INFO)
- [x] 각 엔드포인트에 로깅 추가
  - [x] 요청 로깅
  - [x] 에러 로깅

### Swagger 문서 작성
- [x] 각 엔드포인트에 docstring 추가
  - [x] 설명, 파라미터, 응답 예시
- [x] FastAPI 자동 생성 문서 확인
  - [x] `http://localhost:8001/docs`

### 로컬 서버 실행 테스트
- [x] `uvicorn app.main:app --reload --port 8001` 실행
- [x] Swagger UI에서 각 엔드포인트 테스트
  - [x] POST /api/chat (샘플 쿼리)
  - [x] POST /api/feedback
  - [x] GET /api/health
  - [x] GET /api/stats

### Week 4 마무리
- [x] 코드 리뷰 및 리팩토링
- [x] API 통합 테스트 작성 (pytest) - 18개 테스트 통과
  - [x] `backend/tests/conftest.py` - 테스트 픽스처 및 SQLite 호환 모델
  - [x] `backend/tests/api/test_chat.py` - 채팅 API 테스트 (6개)
  - [x] `backend/tests/api/test_feedback.py` - 피드백 API 테스트 (5개)
  - [x] `backend/tests/api/test_health.py` - 헬스체크 API 테스트 (3개)
  - [x] `backend/tests/api/test_stats.py` - 통계 API 테스트 (4개)
- [ ] Postman 컬렉션 생성 (optional)
- [ ] Git 커밋 (`Week 4 완료: API 엔드포인트`)

---

## 📋 Week 5: 배치 프로세스 구현

### 배치 프로젝트 구조 생성
- [x] `backend/batch/` 디렉토리 확인
- [x] `backend/batch/__init__.py` 생성

### 배치 메인 로직
- [x] `backend/batch/main.py` 작성
  - [x] argparse로 `--source jira/confluence/all` 옵션
  - [x] `run_batch()` 메인 함수
  - [x] SyncHistory 테이블에 시작 기록 (status='running')
  - [x] 예외 처리 및 에러 로깅
  - [x] 완료 시 SyncHistory 업데이트 (status='success')
  - [x] `--dry-run` 옵션 지원
  - [x] `--verbose` 옵션 지원

### Jira 증분 동기화
- [x] `backend/batch/sync_jira.py` 작성
  - [x] `sync_jira_incremental()` 함수
  - [x] sync_history에서 마지막 성공 시간 조회
  - [x] JiraClient로 증분 업데이트 조회 (`updated > last_sync`)
  - [x] PostgreSQL에 업데이트
    - [x] 신규 문서: INSERT
    - [x] 기존 문서: UPDATE (title, content, updated_at, last_synced_at)
  - [x] 통계 반환 (added, updated)

### Confluence 증분 동기화
- [x] `backend/batch/sync_confluence.py` 작성
  - [x] `sync_confluence_incremental()` 함수
  - [x] sync_history에서 마지막 성공 시간 조회
  - [x] ConfluenceClient로 증분 업데이트 조회
  - [x] PostgreSQL에 업데이트
  - [x] 통계 반환
- [x] 배치 로컬 테스트 (dry-run 및 실제 실행 확인)

### 삭제된 문서 감지 및 처리
- [x] `backend/batch/detect_deleted.py` 작성
  - [x] `detect_and_mark_deleted(source)` 함수
  - [x] Jira/Confluence에서 현재 모든 문서 ID 조회
  - [x] PostgreSQL의 문서 ID와 비교
  - [x] 차집합 → `UPDATE documents SET deleted=True`
  - [x] 통계 반환 (jira_deleted, confluence_deleted, total_deleted)

### 텍스트 청킹 및 임베딩
- [x] `backend/batch/process_chunks.py` 작성
  - [x] `process_document_chunks(document_ids)` 함수
  - [x] 각 문서에 대해:
    - [x] 텍스트 청킹 (RecursiveCharacterTextSplitter)
    - [x] 기존 청크 삭제 (document_chunks 테이블)
    - [x] 새 청크 INSERT
    - [x] 임베딩 생성 (배치 100개씩)
    - [x] 벡터 리스트 반환
  - [x] `force_reprocess` 옵션 지원

### FAISS 인덱스 업데이트
- [x] `backend/batch/update_faiss.py` 작성
  - [x] `update_faiss_index()` 함수
  - [x] 로컬 FAISS 인덱스 로드 (없으면 새로 생성)
  - [x] 삭제된 문서의 벡터 제거
    - [x] deleted=True인 문서의 faiss_index_id 조회
    - [x] 인덱스 재빌드로 제거 처리
  - [x] 새 벡터 추가
    - [x] `index.add(vectors)`
    - [x] faiss_index_id를 document_chunks에 업데이트
  - [x] 로컬에 저장
  - [x] `rebuild_faiss_index()` 전체 재빌드 함수
  - [ ] Cloud Storage에 업로드 (Week 8 배포 시 진행)

### 배치 로그 저장
- [x] `backend/batch/main.py`에 로그 저장 로직 추가
  - [x] 배치 시작/종료 시간
  - [x] 처리된 문서 수 (added, updated, deleted)
  - [x] 에러 메시지
  - [x] 로그 파일 생성 (`logs/batch_YYYY-MM-DD.log`)
  - [ ] Cloud Storage에 업로드 (`batch_logs/`) - Week 8 배포 시 진행

### 재시도 로직 구현
- [x] `backend/batch/retry_handler.py` 작성
  - [x] `retry_with_backoff(func, max_retries=3)` 데코레이터
  - [x] 지수 백오프 (initial_delay, max_delay, backoff_factor)
  - [x] 최대 3회 재시도
  - [x] `RetryError`, `RetryContext` 클래스
- [x] sync_jira, sync_confluence에 데코레이터 적용 (`sync_jira_with_retry`, `sync_confluence_with_retry`)

### 배치 CLI 옵션 확장
- [x] `--full-sync`: 청킹 및 FAISS 업데이트 포함
- [x] `--rebuild-faiss`: FAISS 인덱스 전체 재빌드
- [x] `--no-deletions`: 삭제 감지 스킵
- [x] `--no-retry`: 재시도 로직 비활성화

### 배치 로컬 테스트
- [x] 로컬에서 배치 실행
  - [x] `python -m batch.main --source all`
  - [x] `python -m batch.main --source confluence --dry-run`
- [x] 증분 업데이트 확인
  - [x] Jira/Confluence에서 문서 수정 후 재실행
  - [x] PostgreSQL에서 updated_at 확인
- [x] 삭제 감지 확인
  - [x] 테스트 문서 삭제 후 재실행
  - [x] deleted=True 확인
  - [x] Confluence CQL 응답 ID 파싱 버그 수정
- [x] FAISS 인덱스 업데이트 확인 (`--full-sync` 옵션)
  - [x] `python -m batch.main --rebuild-faiss` 테스트

### Week 5 마무리
- [x] 코드 리뷰 및 리팩토링
- [x] 배치 통합 테스트 작성 (31개 테스트 통과)
- [x] 배치 실행 로그 분석
- [x] Git 커밋 (`Week 5 완료: 배치 프로세스`)

---

## 📋 Week 6: 프론트엔드 개발 - Landing Page & Chat (React)

### React 프로젝트 생성
- [x] `frontend/` 디렉토리로 이동
- [x] Vite로 React 프로젝트 생성
  - [x] `npm create vite@latest . -- --template react-ts`
  - [x] React 19, TypeScript 5.8, Vite 7.2
- [x] 의존성 설치
  - [x] `npm install`
  - [x] `npm install axios @tanstack/react-query zustand`
  - [x] `npm install -D tailwindcss postcss autoprefixer @tailwindcss/postcss`
  - [x] `npm install react-router-dom react-markdown`
  - [x] `npm install lucide-react` (아이콘)
  - [x] `npm install tw-animate-css tailwindcss-animate`

### Tailwind CSS 설정
- [x] Tailwind CSS v4 설정 (PostCSS 플러그인 분리)
- [x] `tailwind.config.js` 설정
  - [x] content 경로 추가 (`./src/**/*.{js,ts,jsx,tsx}`)
  - [x] 다크 테마 색상 설정 (shadcn/ui 호환 CSS 변수)
- [x] `postcss.config.js` 설정 (`@tailwindcss/postcss` 사용)
- [x] `src/index.css`에 Tailwind directives 추가
- [x] Tailwind 동작 확인 (`npm run build` 성공)

### shadcn/ui 설치
- [x] `npx shadcn@latest init --base-color neutral --defaults`
- [x] 필요한 컴포넌트 설치
  - [x] `npx shadcn@latest add button`
  - [x] `npx shadcn@latest add input`
  - [x] `npx shadcn@latest add card`
  - [x] `npx shadcn@latest add scroll-area`
  - [x] `npx shadcn@latest add avatar`
  - [x] `npx shadcn@latest add textarea`

### 프로젝트 구조 생성
- [x] `src/` 하위 디렉토리 생성
  - [x] `components/layout/` - 레이아웃 컴포넌트 (Header.tsx, Layout.tsx)
  - [x] `components/landing/` - Landing Page 컴포넌트 (LandingPage.tsx)
  - [x] `components/chat/` - Chat 컴포넌트 (ChatContainer.tsx, ChatInput.tsx, ChatMessage.tsx)
  - [ ] `components/dashboard/` - Dashboard 컴포넌트 (Week 7)
  - [ ] `components/settings/` - Settings 컴포넌트 (Week 7)
  - [x] `hooks/`, `services/`, `store/`, `types/`

### TypeScript 타입 정의
- [x] `src/types/index.ts` 작성
  - [x] `ChatMessage` 인터페이스 (id, role, content, sources, timestamp)
  - [x] `Source` 인터페이스 (doc_id, doc_type, title, url, score)
  - [x] `ChatSession` 인터페이스 (id, messages, createdAt, updatedAt)
  - [x] `ChatRequest`, `ChatResponse` 인터페이스
  - [x] `StatsResponse`, `SearchResponse` 인터페이스
- [ ] `src/types/sync.ts` 작성 (Week 7)
  - [ ] `DataSource` 인터페이스 (type, status, docs_count, last_sync)
  - [ ] `SyncActivity` 인터페이스 (timestamp, event_type, status, description)
  - [ ] `SyncStats` 인터페이스

### Axios API 클라이언트
- [x] `src/services/api.ts` 작성
  - [x] axios 인스턴스 생성
  - [x] baseURL: `import.meta.env.VITE_API_URL`
  - [x] `sendMessage(request: ChatRequest)` 함수
  - [x] `search(query, limit)` 함수
  - [x] `getStats()` 함수
  - [x] `healthCheck()` 함수
  - [ ] `submitFeedback(chatId, rating, comment)` 함수 (Week 7)
  - [ ] `fetchSyncHistory()` 함수 (Week 7)
  - [ ] `testConnection(source, config)` 함수 (Week 7)
  - [ ] `triggerSync(source)` 함수 (Week 7)
  - [ ] `updateSettings(source, settings)` 함수 (Week 7)

### Zustand 상태 관리
- [x] `src/store/chatStore.ts` 작성
  - [x] State: currentSession, sessions, isLoading, error
  - [x] Actions: createSession, addMessage, setLoading, setError, clearCurrentSession, switchSession, deleteSession
  - [x] persist 미들웨어로 localStorage 저장
- [ ] `src/stores/settingsStore.ts` 작성 (Week 7)
  - [ ] State: jiraConfig, confluenceConfig, syncSettings
  - [ ] Actions: updateJiraConfig, updateConfluenceConfig, updateSyncSettings

### React Query 설정
- [x] `src/main.tsx`에 QueryClientProvider 추가
- [x] QueryClient 기본 설정 (staleTime, retry)
- [x] 다크 모드 기본 활성화
- [ ] `src/hooks/useChat.ts` 작성 (Week 7 - 고급 기능)
  - [ ] `useMutation`으로 sendMessage 호출
- [ ] `src/hooks/useFeedback.ts` 작성 (Week 7)
  - [ ] `useMutation`으로 submitFeedback 호출
- [ ] `src/hooks/useSync.ts` 작성 (Week 7)
  - [ ] `useQuery`로 동기화 상태 조회
  - [ ] `useMutation`으로 동기화 트리거

---

### Landing Page 구현 (`/`)

#### Layout 컴포넌트
- [x] `src/components/layout/Layout.tsx` 작성 (간소화된 버전)
  - [x] Header 컴포넌트 (로고, 테마 토글)
  - [x] 메인 콘텐츠 영역
- [x] `src/components/layout/Header.tsx` 작성
  - [x] 로고 (MessageSquare 아이콘 + "Knowledge Base AI")
  - [x] 다크/라이트 모드 토글 버튼

#### LandingPage 컴포넌트 (통합)
- [x] `src/components/landing/LandingPage.tsx` 작성
  - [x] Hero 섹션
    - [x] 타이틀: "Knowledge Base AI Assistant"
    - [x] 설명 텍스트: Jira/Confluence 문서 검색 안내
    - [x] "Start Chatting" CTA 버튼
  - [x] Features 섹션
    - [x] 4개 FeatureCard 통합:
      - [x] AI-Powered Chat (MessageSquare 아이콘)
      - [x] Smart Search (Search 아이콘)
      - [x] Jira & Confluence (Database 아이콘)
      - [x] Source Citations (Sparkles 아이콘)
    - [x] Card 컴포넌트로 스타일링
  - [x] 다크 테마 배경

#### 추후 개선 (Optional)
- [ ] `src/components/landing/HeroSection.tsx` 분리
- [ ] `src/components/landing/FeatureCard.tsx` 분리
- [ ] `src/components/landing/FeaturesSection.tsx` 분리
- [ ] `src/components/landing/HowItWorks.tsx` 작성
- [ ] `src/components/landing/CTASection.tsx` 작성
- [ ] Footer 컴포넌트 추가

---

### Chat Page 구현 (`/chat`)

#### ChatContainer 컴포넌트 (통합)
- [x] `src/components/chat/ChatContainer.tsx` 작성
  - [x] 채팅 헤더 (뒤로가기 버튼, 제목, 삭제 버튼)
  - [x] ScrollArea로 메시지 영역
  - [x] 빈 상태 안내 메시지
  - [x] ChatMessage 컴포넌트 렌더링
  - [x] ChatInput 컴포넌트
  - [x] Zustand 상태 연동
  - [x] API 호출 및 에러 처리
  - [x] 자동 스크롤

#### ChatMessage 컴포넌트
- [x] `src/components/chat/ChatMessage.tsx` 작성
  - [x] Props: message (ChatMessage 타입)
  - [x] AI 메시지: 좌측 정렬, Bot 아바타, muted 배경
  - [x] 사용자 메시지: 우측 정렬, User 아바타, primary 배경
  - [x] react-markdown으로 AI 답변 렌더링
  - [x] 출처 링크 표시 (doc_type, title, ExternalLink 아이콘)
  - [x] 타임스탬프 표시

#### ChatInput 컴포넌트
- [x] `src/components/chat/ChatInput.tsx` 작성
  - [x] Textarea 입력 필드 ("Ask a question...")
  - [x] 전송 버튼 (Send 아이콘)
  - [x] Enter 키 전송 지원 (Shift+Enter는 줄바꿈)
  - [x] 로딩 상태 표시 (Loader2 애니메이션)
  - [x] disabled 상태 지원

#### 추후 개선 (Optional)
- [ ] `src/components/chat/ChatSidebar.tsx` 작성 (채팅 기록 목록)
- [ ] `src/components/chat/ChatHistory.tsx` 작성 (세션 목록)
- [ ] `src/components/chat/SourceCard.tsx` 분리
- [ ] `src/components/chat/FeedbackButtons.tsx` 작성 (👍/👎 버튼)

---

### 환경 변수 설정
- [x] `frontend/.env.example` 파일 생성
  - [x] `VITE_API_URL=http://localhost:8000`
- [ ] `frontend/.env` 파일 생성 (실제 값 입력)

### 라우팅 설정 (간소화)
- [x] `src/App.tsx` 작성
  - [x] useState로 뷰 전환 관리 (landing/chat)
  - [x] Landing → Chat 전환 (`onStartChat`)
  - [x] Chat → Landing 전환 (`onBack`)
- [ ] React Router 설정 (추후 개선)
  - [ ] `/` → LandingPage
  - [ ] `/chat` → ChatPage
  - [ ] `/dashboard` → DashboardPage (Week 7)
  - [ ] `/settings` → SettingsPage (Week 7)

### 로컬 개발 서버 실행
- [x] `npm run dev` 실행 확인
- [x] `http://localhost:5173` 접속 가능
- [x] `npm run build` 빌드 성공 (dist/ 생성)
- [x] Landing Page 동작 확인
  - [x] 모든 섹션 표시
  - [x] "Start Chatting" 버튼 → Chat 화면 이동
- [x] Chat Page 동작 확인
  - [x] 메시지 전송/응답 (백엔드 연동)
  - [x] 출처 카드 표시
  - [x] 에러 처리

### Week 6 마무리
- [x] 기본 프로젝트 구조 완성
- [x] 핵심 컴포넌트 구현 (Layout, Landing, Chat)
- [x] 상태 관리 설정 (Zustand, React Query)
- [x] API 클라이언트 설정 (axios)
- [x] 백엔드 연동 테스트
  - [x] CORS 설정 확인 (access-control-allow-credentials: true)
  - [x] Chat API 테스트 (/api/chat - POST)
  - [x] Stats API 테스트 (/api/stats - GET)
  - [x] Health API 테스트 (/api/health - GET)
- [ ] 코드 리뷰 및 리팩토링 (optional)
- [ ] 컴포넌트 테스트 작성 (Vitest, optional)
- [ ] 반응형 디자인 확인 (모바일, 태블릿, optional)
- [x] Git 커밋 (`Week 6 완료: Landing Page & Chat`)

---

## 📋 Week 7: Dashboard & Settings 페이지

### 차트 라이브러리 설치
- [x] `npm install recharts` (라인 차트, 바 차트 지원)

---

### Dashboard Page 구현 (`/dashboard`)

#### AdminLayout 컴포넌트
- [x] `src/components/layout/AdminLayout.tsx` 작성
  - [x] 상단 네비게이션 (Dashboard, Data Sources, Settings, Logs, Chat help)
  - [x] 프로필 아이콘
  - [x] 다크 테마 배경

#### StatCard 컴포넌트
- [x] `src/components/dashboard/StatCard.tsx` 작성
  - [x] Props: label, value, change (증감률), status
  - [x] 4가지 변형:
    - [x] Overall Sync Status (Healthy/Error 뱃지)
    - [x] Total Documents Synced (숫자 + 증감률)
    - [x] Last Successful Sync (시간)
    - [x] Next Scheduled Sync (시간)
  - [x] 다크 카드 스타일

#### AlertBanner 컴포넌트
- [x] `src/components/dashboard/AlertBanner.tsx` 작성
  - [x] Props: type (error/warning/info), title, message, linkText, linkHref
  - [x] 에러 배너 스타일 (빨간색 테두리)
  - [x] "View Full Logs" 링크
  - [x] 닫기 버튼 (optional)

#### DataSourceCard 컴포넌트
- [x] `src/components/dashboard/DataSourceCard.tsx` 작성
  - [x] Props: source (jira/confluence), status, docsCount, lastSync
  - [x] 로고 이미지 (Jira/Confluence)
  - [x] 상태 표시 (Healthy: 초록색, Error: 빨간색)
  - [x] 동기화된 문서 수
  - [x] 마지막 동기화 시간

#### SyncChart 컴포넌트
- [x] `src/components/dashboard/SyncChart.tsx` 작성
  - [x] Recharts AreaChart 사용 (그라데이션 효과)
  - [x] Props: data (7일간 동기화 데이터)
  - [x] X축: 날짜, Y축: 문서 수
  - [x] 다크 테마 스타일 (녹색 라인)
  - [x] 그라데이션 배경

#### SyncActivityTable 컴포넌트
- [x] `src/components/dashboard/SyncActivityTable.tsx` 작성
  - [x] Props: activities (배열)
  - [x] 컬럼: Timestamp, Event Type, Status, Description
  - [x] Status 뱃지 (Success: 초록, Failed: 빨강, In Progress: 노랑)
  - [ ] 페이지네이션 (optional)
  - [x] 다크 테이블 스타일

#### DashboardHeader 컴포넌트
- [x] `src/components/dashboard/DashboardHeader.tsx` 작성
  - [x] 타이틀: "Data Synchronization Dashboard"
  - [x] 설명 텍스트
  - [x] "Refresh Status" 버튼
  - [x] "Sync Now" 버튼 (주황색)

#### DashboardPage 페이지
- [x] `src/pages/DashboardPage.tsx` 작성
  - [x] AdminLayout 래핑
  - [x] DashboardHeader
  - [x] StatCard 4개 (그리드 레이아웃)
  - [x] AlertBanner (에러 있을 때만)
  - [x] Data Sources 섹션 (2개 카드)
  - [x] SyncChart
  - [x] SyncActivityTable

### Dashboard API 훅
- [x] `src/hooks/useDashboard.ts` 작성
  - [x] `useQuery`로 대시보드 데이터 조회
  - [x] 30초마다 자동 갱신
- [ ] `src/hooks/useSyncTrigger.ts` 작성 (triggerSync은 useDashboard에 통합)
  - [ ] `useMutation`으로 수동 동기화 트리거

---

### Settings Page 구현 (`/settings`)

#### AdminSidebar 컴포넌트
- [x] AdminLayout에 통합 (상단 네비게이션으로 구현)
  - [x] Dashboard, Data Sources, Settings, Logs, Chat 네비게이션
  - [x] 활성 메뉴 하이라이트

#### ConnectionStatus 컴포넌트
- [x] `src/components/settings/ConnectionStatus.tsx` 작성
  - [x] Props: status (connected/error/pending)
  - [x] 아이콘 + 텍스트 ("Connection Status")
  - [x] 상태 뱃지 (Error: 빨강, Connected: 초록, Pending: 노랑)

#### ConnectionSettings 컴포넌트
- [x] `src/components/settings/ConnectionSettings.tsx` 작성
  - [x] Props: source (jira/confluence), config, onUpdate
  - [x] Instance Type: Cloud/Server 라디오 버튼
  - [x] URL 입력 필드
  - [x] Personal Access Token (PAT) 입력 필드 (마스킹)
    - [x] 눈 아이콘으로 토글
  - [x] "Test Connection" 버튼
  - [x] 연결 테스트 결과 표시

#### SyncRules 컴포넌트
- [x] `src/components/settings/SyncRules.tsx` 작성
  - [x] Incremental Sync 토글 스위치
    - [x] 설명: "Only sync new or updated documents"
  - [x] Sync Frequency 드롭다운
    - [x] 옵션: Every 6 hours, Every 12 hours, Every 24 hours, Manual only
  - [x] Last Synced 정보 표시
  - [x] "Sync Now" 버튼 (보라색)

#### DataSourceTabs 컴포넌트
- [x] `src/components/settings/DataSourceTabs.tsx` 작성
  - [x] 탭: Jira | Confluence
  - [x] 활성 탭 하이라이트 (파란색 밑줄)
  - [x] 탭 전환 시 설정 폼 변경

#### SettingsPage 페이지
- [x] `src/pages/SettingsPage.tsx` 작성
  - [x] AdminLayout 래핑 (상단 네비게이션)
  - [x] 메인 영역:
    - [x] 타이틀: "Data Source Management"
    - [x] 설명 텍스트
    - [x] "Save Changes" 버튼 (우상단)
    - [x] AlertBanner (에러 표시)
    - [x] DataSourceTabs
    - [x] ConnectionStatus
    - [x] ConnectionSettings
    - [x] SyncRules

### Settings API 훅
- [x] `src/hooks/useSettings.ts` 작성
  - [x] useState로 현재 설정 관리
  - [x] testConnection 함수 (mock)
  - [x] saveChanges 함수 (mock)
  - [x] triggerSync 함수 (mock)
- [ ] `src/hooks/useConnectionTest.ts` 작성 (useSettings에 통합)
  - [ ] `useMutation`으로 연결 테스트 (실제 API 연동 시)

---

### 백엔드 API 추가 (Dashboard/Settings 지원)

#### Dashboard 엔드포인트
- [x] `GET /api/dashboard/stats` - 대시보드 통계
  - [x] total_documents, jira_count, confluence_count
  - [x] sync_status (healthy/error)
  - [x] last_sync, next_sync
- [x] `GET /api/dashboard/sync-history` - 동기화 이력
  - [x] 최근 7일 동기화 데이터 (차트용)
  - [x] 최근 동기화 활동 목록 (테이블용)
- [x] `POST /api/dashboard/sync` - 수동 동기화 트리거

#### Settings 엔드포인트
- [x] `GET /api/settings/data-sources` - 데이터 소스 설정 조회
- [x] `PUT /api/settings/data-sources/:source` - 데이터 소스 설정 저장
- [x] `POST /api/settings/test-connection` - 연결 테스트
  - [x] Request: { source, url, token }
  - [x] Response: { success, message }

---

### 로컬 테스트
- [x] Dashboard 페이지 (`/dashboard`) 접속
  - [x] 통계 카드 4개 표시 확인
  - [x] Data Sources 카드 표시
  - [x] 동기화 차트 렌더링
  - [x] 활동 테이블 표시
  - [x] "Sync Now" 버튼 동작
- [x] Settings 페이지 (`/settings`) 접속
  - [x] Jira/Confluence 탭 전환
  - [x] 설정 입력 폼 동작
  - [x] "Test Connection" 버튼 동작
  - [x] "Save Changes" 저장 확인
- [x] Backend API 테스트
  - [x] `GET /api/dashboard/stats` 동작 확인
  - [x] `GET /api/dashboard/sync-history` 동작 확인
  - [x] `GET /api/settings/data-sources` 동작 확인

### Week 7 마무리
- [ ] 코드 리뷰 및 리팩토링 (optional)
- [ ] Dashboard/Settings 디자인 개선 (optional)
- [ ] 반응형 디자인 확인 (optional)
- [x] Git 커밋 (`Week 7 완료: Dashboard & Settings`)

---

## 📋 Week 8: GCP 배포

### GCP 프로젝트 및 리소스 생성
- [ ] GCP 콘솔에서 프로젝트 선택/생성
- [ ] Billing 활성화 확인
- [ ] 필요한 API 활성화
  - [ ] Cloud Run API
  - [ ] Cloud SQL Admin API
  - [ ] Cloud Storage API
  - [ ] Secret Manager API
  - [ ] Cloud Scheduler API

### Cloud SQL (PostgreSQL) 생성
- [ ] Cloud SQL 인스턴스 생성
  - [ ] PostgreSQL 15
  - [ ] 리전: asia-northeast3 (서울)
  - [ ] 머신 타입: db-f1-micro (개발용)
  - [ ] 스토리지: 10GB
- [ ] 데이터베이스 생성 (`knowledge_base`)
- [ ] 사용자 생성 (비밀번호 설정)
- [ ] Cloud SQL Proxy 설정 (로컬 테스트용)
- [ ] 로컬에서 연결 테스트
- [ ] `init_db.py` 실행하여 테이블 생성

### Secret Manager에 시크릿 등록
- [ ] `database-url` 시크릿 생성
  - [ ] 값: `postgresql://user:password@/dbname?host=/cloudsql/...`
- [ ] `azure-openai-api-key` 시크릿 생성
- [ ] `azure-openai-endpoint` 시크릿 생성
- [ ] `jira-api-token` 시크릿 생성
- [ ] `confluence-api-token` 시크릿 생성

### Dockerfile 작성 (Main API)
- [ ] `backend/Dockerfile.api` 작성
  - [ ] FROM python:3.11-slim
  - [ ] WORKDIR /app
  - [ ] COPY requirements.txt
  - [ ] RUN pip install
  - [ ] COPY app/
  - [ ] CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
- [ ] 로컬에서 Docker 빌드 테스트
  - [ ] `docker build -f Dockerfile.api -t kb-api .`
  - [ ] `docker run -p 8000:8000 kb-api`

### Dockerfile 작성 (Batch)
- [ ] `backend/Dockerfile.batch` 작성
  - [ ] FROM python:3.11-slim
  - [ ] WORKDIR /app
  - [ ] COPY requirements.txt
  - [ ] RUN pip install
  - [ ] COPY app/, batch/
  - [ ] CMD python -m batch.main --source all
- [ ] 로컬에서 Docker 빌드 테스트

### Cloud Run 서비스 배포 (Main API)
- [ ] Artifact Registry 레포지토리 생성
- [ ] Docker 이미지 빌드 및 푸시
  - [ ] `docker build -t gcr.io/PROJECT_ID/kb-api:latest -f Dockerfile.api .`
  - [ ] `docker push gcr.io/PROJECT_ID/kb-api:latest`
- [ ] Cloud Run 서비스 생성
  - [ ] 이미지: gcr.io/PROJECT_ID/kb-api:latest
  - [ ] 리전: asia-northeast3
  - [ ] 메모리: 2GB, CPU: 2
  - [ ] Min instances: 1, Max instances: 10
  - [ ] 환경 변수: Secret Manager에서 주입
  - [ ] Cloud SQL 연결 설정
- [ ] 배포 확인
  - [ ] Cloud Run URL 접속
  - [ ] `/api/health` 엔드포인트 테스트

### Cloud Run Job 생성 (Batch)
- [ ] Docker 이미지 빌드 및 푸시
  - [ ] `docker build -t gcr.io/PROJECT_ID/kb-batch:latest -f Dockerfile.batch .`
  - [ ] `docker push gcr.io/PROJECT_ID/kb-batch:latest`
- [ ] Cloud Run Job 생성
  - [ ] 이미지: gcr.io/PROJECT_ID/kb-batch:latest
  - [ ] 리전: asia-northeast3
  - [ ] 환경 변수: Secret Manager에서 주입
  - [ ] Cloud SQL 연결, Cloud Storage 접근 권한
  - [ ] Task count: 1
  - [ ] Max retries: 3
- [ ] 수동 실행 테스트
  - [ ] gcloud CLI로 Job 실행
  - [ ] 로그 확인 (Cloud Logging)

### Cloud Scheduler 설정
- [ ] Cloud Scheduler Job 생성
  - [ ] 이름: `knowledge-base-daily-sync`
  - [ ] 리전: asia-northeast3
  - [ ] 스케줄: `0 6 * * *` (매일 오전 6시)
  - [ ] 타임존: Asia/Seoul
  - [ ] Target: Cloud Run Job (`kb-batch`)
  - [ ] 서비스 계정: 적절한 권한 부여
- [ ] 첫 실행 대기 또는 수동 트리거
- [ ] 실행 이력 확인

### React 빌드 및 배포
- [ ] `frontend/` 디렉토리에서 빌드
  - [ ] `.env.production` 생성
    - [ ] `VITE_API_BASE_URL=https://kb-api-xxxxx.run.app`
  - [ ] `npm run build`
  - [ ] `dist/` 디렉토리 생성 확인
- [ ] 배포 옵션 선택
  - [ ] **Option A**: Cloud Run (컨테이너)
    - [ ] Nginx Dockerfile 작성
    - [ ] Docker 빌드 및 푸시
    - [ ] Cloud Run 서비스 배포
  - [ ] **Option B**: Vercel (권장)
    - [ ] Vercel CLI 설치 (`npm i -g vercel`)
    - [ ] `vercel login`
    - [ ] `vercel` (배포)
    - [ ] 환경 변수 설정 (Vercel Dashboard)
- [ ] 배포 확인
  - [ ] 프론트엔드 URL 접속
  - [ ] 채팅 기능 테스트
  - [ ] 통계 페이지 테스트

### 커스텀 도메인 설정 (Optional)
- [ ] 도메인 구매 (예: kb.yourdomain.com)
- [ ] Cloud Run에 커스텀 도메인 매핑
- [ ] SSL 인증서 자동 프로비저닝
- [ ] DNS 레코드 설정

### Week 8 마무리
- [ ] 배포 문서 작성 (`docs/DEPLOYMENT.md`)
- [ ] 프로덕션 환경 설정 확인
- [ ] 비용 모니터링 설정 (Budget Alerts)
- [ ] Git 커밋 (`Week 8 완료: GCP 배포`)

---

## 📋 Week 9: 테스트 및 최적화

### 단위 테스트 작성 (pytest)
- [ ] `backend/tests/unit/test_jira_client.py`
- [ ] `backend/tests/unit/test_confluence_client.py`
- [ ] `backend/tests/unit/test_embedding_service.py`
- [ ] `backend/tests/unit/test_vector_db_service.py`
- [ ] `backend/tests/unit/test_rag_service.py`
- [ ] `backend/tests/unit/test_agents.py` (각 에이전트)
- [ ] 테스트 실행: `pytest tests/unit/ -v`
- [ ] 커버리지 확인: `pytest --cov=app --cov-report=html`

### 통합 테스트 작성
- [ ] `backend/tests/integration/test_workflow.py`
  - [ ] End-to-end 워크플로우 테스트
- [ ] `backend/tests/integration/test_api.py`
  - [ ] FastAPI 엔드포인트 테스트 (TestClient)
- [ ] `backend/tests/integration/test_batch.py`
  - [ ] 배치 프로세스 테스트
- [ ] 테스트 실행: `pytest tests/integration/ -v`

### 배치 프로세스 통합 테스트
- [ ] 로컬에서 전체 배치 실행
  - [ ] 데이터 수집 → 청킹 → 임베딩 → FAISS 업데이트
- [ ] 증분 업데이트 시나리오 테스트
  - [ ] Jira/Confluence에서 문서 수정
  - [ ] 배치 재실행
  - [ ] 변경사항 반영 확인
- [ ] 삭제 시나리오 테스트
  - [ ] 문서 삭제 후 배치 실행
  - [ ] deleted=True 확인

### API 부하 테스트 (Locust)
- [ ] `backend/tests/load/locustfile.py` 작성
  - [ ] POST /api/chat 부하 테스트
  - [ ] 동시 사용자 100명 시뮬레이션
- [ ] Locust 실행
  - [ ] `locust -f tests/load/locustfile.py`
- [ ] 결과 분석
  - [ ] 평균 응답 시간
  - [ ] 처리량 (RPS)
  - [ ] 에러율

### 임베딩 배치 크기 최적화
- [ ] 배치 크기별 성능 테스트 (50, 100, 200)
- [ ] 최적 배치 크기 선택 (속도 vs 메모리)

### FAISS 검색 속도 최적화
- [ ] FAISS 인덱스 타입 변경 고려
  - [ ] IndexFlatL2 (현재): 정확하지만 느림
  - [ ] IndexIVFFlat: 속도 개선, 약간의 정확도 손실
- [ ] 인덱스 크기별 성능 측정
- [ ] 필요시 인덱스 타입 변경

### 메모리 사용량 모니터링
- [ ] `memory_profiler` 설치
- [ ] 배치 프로세스 메모리 프로파일링
- [ ] 메모리 누수 확인 및 수정
- [ ] Cloud Run 메모리 설정 조정 (필요시)

### 에러 로깅 및 알림 설정
- [ ] Cloud Logging 필터 생성
  - [ ] ERROR 레벨 로그만 필터링
- [ ] Cloud Monitoring 알림 정책 생성
  - [ ] 배치 실패 시 이메일 알림
  - [ ] API 에러율 5% 초과 시 알림
- [ ] Slack 웹훅 통합 (Optional)
  - [ ] 배치 완료/실패 알림
  - [ ] 통계 요약 전송

### 성능 튜닝 체크리스트
- [ ] PostgreSQL 인덱스 최적화
  - [ ] EXPLAIN ANALYZE로 쿼리 분석
  - [ ] 필요시 추가 인덱스 생성
- [ ] FastAPI 응답 캐싱 (Optional)
  - [ ] Redis 도입 고려
- [ ] LLM 호출 최적화
  - [ ] 프롬프트 길이 최소화
  - [ ] Temperature, Max tokens 조정

### Week 9 마무리
- [ ] 테스트 커버리지 80% 이상 달성
- [ ] 성능 테스트 결과 문서화
- [ ] 최적화 결과 정리
- [ ] Git 커밋 (`Week 9 완료: 테스트 및 최적화`)

---

## 📋 Week 10: 문서화 및 런칭

### README.md 작성
- [ ] 프로젝트 개요
- [ ] 주요 기능
- [ ] 아키텍처 다이어그램
- [ ] 기술 스택
- [ ] 로컬 개발 환경 설정
  - [ ] 사전 요구사항
  - [ ] 설치 방법
  - [ ] 환경 변수 설정
  - [ ] 실행 방법
- [ ] 배포 방법 (간략)
- [ ] 라이선스

### CLAUDE.md 작성 (개발 가이드)
- [ ] 프로젝트 구조 설명
- [ ] 각 디렉토리/파일 역할
- [ ] 개발 워크플로우
- [ ] 코딩 컨벤션
- [ ] 테스트 작성 가이드
- [ ] 트러블슈팅 가이드
- [ ] 주요 의사결정 기록 (ADR)

### API 문서 완성
- [ ] `docs/API.md` 작성
  - [ ] 각 엔드포인트 상세 설명
  - [ ] Request/Response 예시
  - [ ] 에러 코드
  - [ ] 인증 방법 (추후)
- [ ] Swagger UI 스크린샷 추가

### 아키텍처 문서
- [ ] `docs/ARCHITECTURE.md` 작성
  - [ ] 시스템 아키텍처 다이어그램
  - [ ] 데이터 플로우
  - [ ] LangGraph 워크플로우 설명
  - [ ] 배치 프로세스 상세
  - [ ] 기술적 결정 사항 (Why GCP, Why FAISS 등)

### 배포 가이드
- [ ] `docs/DEPLOYMENT.md` 작성
  - [ ] GCP 프로젝트 생성 단계
  - [ ] Cloud SQL 설정
  - [ ] Secret Manager 설정
  - [ ] Cloud Run 배포 단계
  - [ ] Cloud Scheduler 설정
  - [ ] 프론트엔드 배포 (Vercel)
  - [ ] 비용 최적화 팁

### 사용자 가이드
- [ ] `docs/USER_GUIDE.md` 작성
  - [ ] 채팅 사용 방법
  - [ ] 출처 링크 활용
  - [ ] 피드백 제공 방법
  - [ ] FAQ

### 관리자 매뉴얼
- [ ] `docs/ADMIN_GUIDE.md` 작성
  - [ ] 통계 대시보드 해석
  - [ ] 배치 모니터링
  - [ ] 데이터 품질 관리
  - [ ] 장애 대응 절차
  - [ ] 백업 및 복구

### 배치 모니터링 대시보드 설정
- [ ] Cloud Monitoring 대시보드 생성
  - [ ] 배치 실행 성공률
  - [ ] 처리된 문서 수 (시계열)
  - [ ] API 응답 시간
  - [ ] 에러율
- [ ] 대시보드 스크린샷 문서에 추가

### 베타 사용자 테스트
- [ ] 베타 테스터 5-10명 모집
- [ ] 테스트 시나리오 작성
  - [ ] 일반적인 질문 10개
  - [ ] 엣지 케이스 5개
- [ ] 피드백 수집 양식 준비 (Google Forms)
- [ ] 베타 테스트 실시 (1주일)
- [ ] 피드백 분석

### 피드백 반영 및 개선
- [ ] 베타 테스터 피드백 리뷰
- [ ] 버그 수정
- [ ] UX 개선 사항 반영
- [ ] 문서 업데이트

### 런칭 준비 체크리스트
- [ ] 모든 테스트 통과 확인
- [ ] 프로덕션 환경 설정 재확인
- [ ] 배치 스케줄러 동작 확인 (최소 3일)
- [ ] 모니터링 알림 동작 확인
- [ ] 문서 최종 검토
- [ ] 백업 계획 수립
- [ ] 롤백 계획 수립

### 정식 런칭 🚀
- [ ] 런칭 공지
- [ ] 사용자 교육 세션 (Optional)
- [ ] 초기 사용자 모니터링 (첫 1주일)
- [ ] 피드백 지속 수집

### Week 10 마무리
- [ ] 모든 문서 최종 커밋
- [ ] GitHub 저장소 README 업데이트
- [ ] Git 태그 생성 (`v1.0.0`)
- [ ] 프로젝트 회고 (Retrospective)
- [ ] 축하 🎉

---

## 📋 Phase 2: 추후 개선 사항 (백로그)

### 인증 및 권한
- [ ] Google OAuth 2.0 통합
- [ ] 사용자 관리 시스템
- [ ] Jira/Confluence 권한 상속
- [ ] Admin 역할 관리

### 고급 기능
- [ ] 멀티턴 대화 (대화 컨텍스트 유지)
- [ ] 문서 요약 기능
- [ ] 스트리밍 응답 (SSE)
- [ ] 음성 입력/출력
- [ ] 다국어 지원

### 모니터링 및 분석
- [ ] Google Analytics 4 통합
- [ ] 사용자 행동 분석
- [ ] A/B 테스트 시스템
- [ ] 품질 지표 자동 리포팅

### 확장성
- [ ] Slack 봇 통합
- [ ] Microsoft Teams 봇 통합
- [ ] 모바일 앱 (React Native)
- [ ] GraphQL API

### 성능 개선
- [ ] Redis 캐싱 도입
- [ ] FAISS GPU 버전
- [ ] Batch 병렬 처리
- [ ] CDN 도입 (프론트엔드)

---

**작성일**: 2025-01-24
**프로젝트 위치**: `/Users/sunchulkim/src/knowledge-base-ai-chatbot/`
**예상 완료**: Week 10 (약 2.5개월)
