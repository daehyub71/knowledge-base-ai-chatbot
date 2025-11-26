"""Test script for LangGraph workflow end-to-end testing."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.workflow import run_workflow

# Sample queries for testing
# 5 queries that should be answered by RAG (Jira/Confluence docs)
RAG_QUERIES = [
    "Confluence API 사용법을 알려주세요",
    "프로젝트 문서화 가이드라인",
    "시스템 아키텍처 설계 방법",
    "Jira 이슈 관리 프로세스",
    "팀 협업 도구 사용 방법",
]

# 5 queries that should use LLM fallback (general knowledge)
FALLBACK_QUERIES = [
    "파이썬에서 리스트와 튜플의 차이점은?",
    "HTTP와 HTTPS의 차이",
    "마이크로서비스 아키텍처란?",
    "안녕하세요",
    "오늘 날씨가 어때요?",
]


def test_single_query(query: str, expected_type: str | None = None) -> dict:
    """Test a single query and return results.

    Args:
        query: The query to test
        expected_type: Expected response type ("rag" or "llm_fallback")

    Returns:
        Dictionary with test results
    """
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print("-" * 60)

    result = run_workflow(query)

    response_type = result.get("response_type", "unknown")
    response = result.get("response", "")
    sources = result.get("sources", [])
    error = result.get("error")

    # Print results
    print(f"Response Type: {response_type}")
    print(f"Sources: {len(sources)}")

    if sources:
        for i, source in enumerate(sources, 1):
            print(f"  {i}. [{source.get('doc_type', 'N/A')}] {source.get('title', 'N/A')}")

    print(f"\nResponse Preview:")
    # Show first 300 chars of response
    preview = response[:300].replace('\n', ' ')
    print(f"  {preview}...")

    if error:
        print(f"\n⚠️  Error: {error}")

    # Check if response matches expected type
    if expected_type:
        match = response_type == expected_type
        status = "✅" if match else "❌"
        print(f"\nExpected: {expected_type} | Actual: {response_type} {status}")
        result["match"] = match
    else:
        result["match"] = None

    return result


def run_rag_tests():
    """Run tests with queries that should use RAG."""
    print("\n" + "=" * 60)
    print("RAG 응답 테스트 (회사 문서 기반)")
    print("=" * 60)

    results = []
    for query in RAG_QUERIES:
        result = test_single_query(query, expected_type="rag")
        results.append(result)

    return results


def run_fallback_tests():
    """Run tests with queries that should use LLM fallback."""
    print("\n" + "=" * 60)
    print("LLM Fallback 테스트 (일반 지식)")
    print("=" * 60)

    results = []
    for query in FALLBACK_QUERIES:
        result = test_single_query(query, expected_type="llm_fallback")
        results.append(result)

    return results


def print_summary(rag_results: list, fallback_results: list):
    """Print test summary."""
    print("\n" + "=" * 60)
    print("테스트 요약")
    print("=" * 60)

    # RAG test stats
    rag_matches = sum(1 for r in rag_results if r.get("match") is True)
    rag_total = len(rag_results)
    print(f"\nRAG 테스트: {rag_matches}/{rag_total} 성공")

    for i, r in enumerate(rag_results, 1):
        status = "✅" if r.get("match") else "❌"
        print(f"  {i}. {status} {r.get('response_type', 'N/A')}")

    # Fallback test stats
    fallback_matches = sum(1 for r in fallback_results if r.get("match") is True)
    fallback_total = len(fallback_results)
    print(f"\nFallback 테스트: {fallback_matches}/{fallback_total} 성공")

    for i, r in enumerate(fallback_results, 1):
        status = "✅" if r.get("match") else "❌"
        print(f"  {i}. {status} {r.get('response_type', 'N/A')}")

    # Overall
    total_matches = rag_matches + fallback_matches
    total_tests = rag_total + fallback_total
    success_rate = (total_matches / total_tests * 100) if total_tests > 0 else 0

    print(f"\n전체 성공률: {total_matches}/{total_tests} ({success_rate:.1f}%)")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test LangGraph workflow")
    parser.add_argument(
        "--query",
        type=str,
        help="Single query to test (skips full test suite)",
    )
    parser.add_argument(
        "--rag-only",
        action="store_true",
        help="Run only RAG tests",
    )
    parser.add_argument(
        "--fallback-only",
        action="store_true",
        help="Run only fallback tests",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("Knowledge Base AI Chatbot - 워크플로우 테스트")
    print("=" * 60)

    if args.query:
        # Single query test
        test_single_query(args.query)
    else:
        # Full test suite
        rag_results = []
        fallback_results = []

        if not args.fallback_only:
            rag_results = run_rag_tests()

        if not args.rag_only:
            fallback_results = run_fallback_tests()

        print_summary(rag_results, fallback_results)

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
