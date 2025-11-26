"""Test script for RAG search functionality."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.services.rag_service import RAGService

# Default index path
DEFAULT_INDEX_PATH = Path(__file__).parent.parent / "data" / "vector_db" / "faiss.index"

# Sample queries for testing
SAMPLE_QUERIES = [
    # 기술 관련 질문
    "API 응답 시간을 개선하는 방법",
    "데이터베이스 성능 최적화",
    "캐싱 전략 및 구현",
    "마이크로서비스 아키텍처 설계",
    "Docker 컨테이너 배포",
    # 프로젝트 관련 질문
    "프로젝트 일정 관리",
    "버그 수정 프로세스",
    "코드 리뷰 가이드라인",
    # 일반적인 질문
    "회의록 작성 방법",
    "팀 협업 도구 사용법",
]


def test_search_with_sample_queries(rag_service: RAGService):
    """Test search with sample queries."""
    print("=" * 60)
    print("샘플 쿼리 검색 테스트")
    print("=" * 60)

    for i, query in enumerate(SAMPLE_QUERIES, 1):
        print(f"\n[쿼리 {i}] {query}")
        print("-" * 50)

        results = rag_service.search_documents(query, top_k=3)

        if not results:
            print("  결과 없음")
            continue

        for j, result in enumerate(results, 1):
            print(f"  {j}. [{result['doc_type']}] {result['title']}")
            print(f"     유사도: {result['similarity_score']:.4f}")
            print(f"     URL: {result['url']}")
            if result.get('chunk_text'):
                preview = result['chunk_text'][:100].replace('\n', ' ')
                print(f"     미리보기: {preview}...")


def test_search_by_doc_type(rag_service: RAGService):
    """Test search filtered by document type."""
    print("\n" + "=" * 60)
    print("문서 유형별 검색 테스트")
    print("=" * 60)

    test_query = "시스템 설계 및 아키텍처"

    # Search Jira only
    print(f"\n[Jira 검색] {test_query}")
    print("-" * 50)
    jira_results = rag_service.search_jira(test_query, top_k=3)
    if jira_results:
        for j, result in enumerate(jira_results, 1):
            print(f"  {j}. {result['title']} (유사도: {result['similarity_score']:.4f})")
    else:
        print("  Jira 결과 없음")

    # Search Confluence only
    print(f"\n[Confluence 검색] {test_query}")
    print("-" * 50)
    confluence_results = rag_service.search_confluence(test_query, top_k=3)
    if confluence_results:
        for j, result in enumerate(confluence_results, 1):
            print(f"  {j}. {result['title']} (유사도: {result['similarity_score']:.4f})")
    else:
        print("  Confluence 결과 없음")


def test_search_with_threshold(rag_service: RAGService):
    """Test search with score threshold."""
    print("\n" + "=" * 60)
    print("유사도 임계값 테스트")
    print("=" * 60)

    test_query = "API 성능 최적화"
    thresholds = [0.3, 0.5, 0.7]

    for threshold in thresholds:
        print(f"\n[임계값 {threshold}] {test_query}")
        print("-" * 50)

        results = rag_service.search_documents(
            test_query,
            top_k=5,
            score_threshold=threshold,
        )

        print(f"  결과 수: {len(results)}")
        for j, result in enumerate(results, 1):
            print(f"  {j}. {result['title']} (유사도: {result['similarity_score']:.4f})")


def test_index_stats(rag_service: RAGService):
    """Display index statistics."""
    print("\n" + "=" * 60)
    print("인덱스 통계")
    print("=" * 60)

    stats = rag_service.get_index_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test RAG search functionality")
    parser.add_argument(
        "--index-path",
        type=str,
        default=str(DEFAULT_INDEX_PATH),
        help=f"Path to FAISS index (default: {DEFAULT_INDEX_PATH})",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Single query to test (skips sample queries)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to return (default: 5)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("Knowledge Base AI Chatbot - 검색 테스트")
    print("=" * 60)
    print(f"인덱스 경로: {args.index_path}")

    # Check if index exists
    index_path = Path(args.index_path)
    if not index_path.exists():
        print(f"\n❌ 인덱스 파일이 없습니다: {index_path}")
        print("먼저 'python scripts/build_vector_db.py'를 실행하세요.")
        sys.exit(1)

    # Initialize RAG service
    try:
        rag_service = RAGService(vector_db_path=str(index_path))
        print("✅ RAGService 초기화 완료")
    except Exception as e:
        print(f"\n❌ RAGService 초기화 실패: {e}")
        sys.exit(1)

    # Run tests
    if args.query:
        # Single query test
        print(f"\n[단일 쿼리 테스트] {args.query}")
        print("-" * 50)

        results = rag_service.search_documents(args.query, top_k=args.top_k)

        if not results:
            print("결과 없음")
        else:
            for j, result in enumerate(results, 1):
                print(f"\n{j}. [{result['doc_type']}] {result['title']}")
                print(f"   유사도: {result['similarity_score']:.4f}")
                print(f"   거리: {result['distance']:.4f}")
                print(f"   URL: {result['url']}")
                print(f"   작성자: {result['author']}")
                print(f"   업데이트: {result['updated_at']}")
                if result.get('chunk_text'):
                    print(f"   청크 텍스트:\n   {result['chunk_text']}")
    else:
        # Full test suite
        test_index_stats(rag_service)
        test_search_with_sample_queries(rag_service)
        test_search_by_doc_type(rag_service)
        test_search_with_threshold(rag_service)

    print("\n" + "=" * 60)
    print("검색 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
