"""Test script for text chunking and embedding services."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.text_splitter import TextSplitter, chunk_documents
from app.core.services.embedding_service import EmbeddingService, EMBEDDING_DIMENSION


# Sample documents for testing
SAMPLE_DOCUMENTS = [
    {
        "doc_id": "JIRA-123",
        "doc_type": "jira_issue",
        "title": "API 응답 시간 개선",
        "content": """
        API 응답 시간이 너무 느립니다. 현재 평균 응답 시간이 3초 이상 걸리고 있습니다.

        문제 분석:
        1. 데이터베이스 쿼리 최적화 필요
        2. 캐싱 레이어 미구현
        3. N+1 쿼리 문제 발견

        해결 방안:
        - Redis 캐싱 도입
        - 쿼리 인덱스 추가
        - Eager loading 적용

        예상 효과:
        응답 시간을 500ms 이하로 개선할 수 있을 것으로 예상됩니다.
        캐싱 적중률 80% 이상 달성 시 서버 부하도 크게 감소할 것입니다.
        """,
        "url": "https://jira.example.com/browse/JIRA-123",
        "author": "개발자A",
        "created_at": "2024-01-15",
        "updated_at": "2024-01-20",
        "metadata": {"priority": "high", "status": "in_progress"},
    },
    {
        "doc_id": "CONF-456",
        "doc_type": "confluence_page",
        "title": "시스템 아키텍처 문서",
        "content": """
        Knowledge Base AI Chatbot 시스템 아키텍처

        1. 개요
        이 시스템은 Jira와 Confluence의 데이터를 수집하여 AI 기반 검색 및 질의응답 기능을 제공합니다.

        2. 구성 요소
        - Frontend: React + TypeScript
        - Backend: FastAPI + PostgreSQL
        - AI: OpenAI GPT-4o + Embeddings
        - Vector DB: pgvector

        3. 데이터 흐름
        사용자 질문 → 임베딩 변환 → 벡터 유사도 검색 → 관련 문서 추출 → LLM 답변 생성

        4. 보안
        - OAuth 2.0 인증
        - API 키 암호화 저장
        - HTTPS 통신

        5. 확장성
        - 수평 확장 가능한 아키텍처
        - 마이크로서비스 패턴 적용 가능
        """,
        "url": "https://confluence.example.com/pages/CONF-456",
        "author": "아키텍트B",
        "created_at": "2024-01-10",
        "updated_at": "2024-01-18",
        "metadata": {"space": "DEV", "labels": ["architecture", "ai"]},
    },
]


def test_text_splitter():
    """Test TextSplitter functionality."""
    print("=" * 60)
    print("텍스트 청킹 테스트")
    print("=" * 60)

    splitter = TextSplitter(chunk_size=500, chunk_overlap=100)

    # Test split_text
    sample_text = SAMPLE_DOCUMENTS[0]["content"]
    chunks = splitter.split_text(sample_text)

    print(f"\n[split_text 테스트]")
    print(f"원본 텍스트 길이: {len(sample_text)} 문자")
    print(f"생성된 청크 수: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"  청크 {i+1}: {len(chunk)} 문자")

    # Test split_document
    print(f"\n[split_document 테스트]")
    doc_chunks = splitter.split_document(SAMPLE_DOCUMENTS[0])
    print(f"문서 '{SAMPLE_DOCUMENTS[0]['title']}' 청킹 결과:")
    print(f"  총 청크 수: {len(doc_chunks)}")
    for chunk in doc_chunks:
        print(f"  - 청크 {chunk['chunk_index']}: {chunk['chunk_size']} 문자 (총 {chunk['total_chunks']}개 중)")

    # Test chunk_documents (batch)
    print(f"\n[chunk_documents 배치 테스트]")
    all_chunks = chunk_documents(SAMPLE_DOCUMENTS, chunk_size=500, chunk_overlap=100)
    print(f"총 문서 수: {len(SAMPLE_DOCUMENTS)}")
    print(f"총 청크 수: {len(all_chunks)}")

    # Group by document
    by_doc = {}
    for chunk in all_chunks:
        doc_id = chunk["doc_id"]
        if doc_id not in by_doc:
            by_doc[doc_id] = []
        by_doc[doc_id].append(chunk)

    for doc_id, chunks in by_doc.items():
        print(f"  {doc_id}: {len(chunks)} 청크")

    print("\n✅ 텍스트 청킹 테스트 완료!")
    return all_chunks


def test_embedding_service(chunks: list[dict] = None):
    """Test EmbeddingService functionality."""
    print("\n" + "=" * 60)
    print("임베딩 서비스 테스트")
    print("=" * 60)

    try:
        service = EmbeddingService()
        print(f"임베딩 모델: {service.model}")
        print(f"임베딩 차원: {EMBEDDING_DIMENSION}")
    except Exception as e:
        print(f"❌ EmbeddingService 초기화 실패: {e}")
        print("   .env 파일에 OPENAI_API_KEY 또는 Azure OpenAI 설정을 확인하세요.")
        return

    # Test connection
    print("\n[연결 테스트]")
    if service.test_connection():
        print("✅ OpenAI API 연결 성공!")
    else:
        print("❌ OpenAI API 연결 실패")
        return

    # Test single embedding
    print("\n[단일 임베딩 테스트]")
    test_texts = [
        "API 응답 시간 최적화",
        "데이터베이스 인덱스 튜닝",
        "Redis 캐싱 구현",
        "시스템 아키텍처 설계",
        "마이크로서비스 패턴",
    ]

    for text in test_texts:
        embedding = service.get_embedding(text)
        if embedding:
            print(f"  '{text}' → 벡터 차원: {len(embedding)}")
        else:
            print(f"  '{text}' → 임베딩 생성 실패")

    # Test batch embedding
    print("\n[배치 임베딩 테스트]")
    embeddings = service.get_embeddings_batch(test_texts)
    print(f"입력 텍스트 수: {len(test_texts)}")
    print(f"생성된 임베딩 수: {len(embeddings)}")
    print(f"각 임베딩 차원: {len(embeddings[0]) if embeddings else 'N/A'}")

    # Test embed_chunks (if chunks provided)
    if chunks:
        print("\n[청크 임베딩 테스트]")
        # Only embed first 3 chunks to save API calls
        sample_chunks = chunks[:3]
        embedded_chunks = service.embed_chunks(sample_chunks)
        print(f"청크 수: {len(sample_chunks)}")
        for chunk in embedded_chunks:
            has_embedding = "embedding" in chunk and chunk["embedding"] is not None
            embedding_dim = len(chunk["embedding"]) if has_embedding else 0
            print(f"  청크 '{chunk['doc_id']}' #{chunk['chunk_index']}: "
                  f"임베딩 {'있음' if has_embedding else '없음'} ({embedding_dim} 차원)")

    print("\n✅ 임베딩 서비스 테스트 완료!")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Knowledge Base AI Chatbot - 청킹 & 임베딩 테스트")
    print("=" * 60)

    # Test chunking
    chunks = test_text_splitter()

    # Test embedding
    test_embedding_service(chunks)

    print("\n" + "=" * 60)
    print("모든 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
