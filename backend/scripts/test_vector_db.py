"""Test script for FAISS vector database service."""

import sys
import tempfile
from pathlib import Path

import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.services.vector_db_service import VectorDBService


def test_create_index():
    """Test creating a new FAISS index."""
    print("=" * 60)
    print("FAISS 인덱스 생성 테스트")
    print("=" * 60)

    service = VectorDBService(dimension=128)  # Use smaller dimension for testing
    index = service.create_index()

    print(f"인덱스 생성 완료")
    print(f"  차원: {service.dimension}")
    print(f"  벡터 수: {index.ntotal}")
    print(f"  인덱스 타입: {type(index).__name__}")

    stats = service.get_stats()
    print(f"\n통계: {stats}")

    print("\n✅ 인덱스 생성 테스트 완료!")
    return service


def test_add_vectors(service: VectorDBService):
    """Test adding vectors to the index."""
    print("\n" + "=" * 60)
    print("벡터 추가 테스트")
    print("=" * 60)

    # Generate 10 random vectors
    np.random.seed(42)  # For reproducibility
    vectors = np.random.rand(10, 128).astype(np.float32)

    # Create metadata for each vector
    metadata = [
        {"doc_id": f"DOC-{i+1}", "title": f"문서 {i+1}", "doc_type": "test"}
        for i in range(10)
    ]

    # Add vectors
    index_ids = service.add_vectors(vectors, metadata)

    print(f"추가된 벡터 수: {len(index_ids)}")
    print(f"할당된 인덱스 ID: {index_ids}")
    print(f"총 벡터 수: {service.index.ntotal}")
    print(f"메타데이터 수: {len(service.metadata)}")

    # Print metadata sample
    print(f"\n메타데이터 샘플:")
    for i, meta in enumerate(service.metadata[:3]):
        print(f"  {i}: {meta}")

    print("\n✅ 벡터 추가 테스트 완료!")
    return vectors


def test_search(service: VectorDBService, vectors: np.ndarray):
    """Test vector similarity search."""
    print("\n" + "=" * 60)
    print("유사도 검색 테스트")
    print("=" * 60)

    # Use first vector as query
    query_vector = vectors[0]

    # Search for top 5 similar vectors
    results = service.search(query_vector, k=5)

    print(f"쿼리: 첫 번째 벡터 (DOC-1)")
    print(f"결과 수: {len(results)}")
    print(f"\n검색 결과:")
    for idx, distance, meta in results:
        print(f"  인덱스 {idx}: 거리={distance:.4f}, 메타데이터={meta}")

    # Test search_with_scores
    print(f"\n유사도 점수 포함 검색:")
    scored_results = service.search_with_scores(query_vector, k=5)
    for result in scored_results:
        print(f"  인덱스 {result['index_id']}: "
              f"거리={result['distance']:.4f}, "
              f"유사도={result['similarity_score']:.4f}")

    print("\n✅ 유사도 검색 테스트 완료!")


def test_save_load(service: VectorDBService):
    """Test saving and loading the index."""
    print("\n" + "=" * 60)
    print("인덱스 저장/로드 테스트")
    print("=" * 60)

    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = Path(tmpdir) / "test_index.faiss"

        # Save index
        service.save_index(index_path)
        print(f"인덱스 저장 완료: {index_path}")
        print(f"메타데이터 저장 완료: {index_path.with_suffix('.pkl')}")

        # Check files exist
        assert index_path.exists(), "인덱스 파일이 없습니다"
        assert index_path.with_suffix(".pkl").exists(), "메타데이터 파일이 없습니다"

        # Create new service and load
        new_service = VectorDBService()
        new_service.load_index(index_path)

        print(f"\n인덱스 로드 완료")
        print(f"  로드된 벡터 수: {new_service.index.ntotal}")
        print(f"  로드된 메타데이터 수: {len(new_service.metadata)}")
        print(f"  차원: {new_service.dimension}")

        # Verify data
        assert new_service.index.ntotal == service.index.ntotal
        assert len(new_service.metadata) == len(service.metadata)

    print("\n✅ 인덱스 저장/로드 테스트 완료!")


def test_remove_vectors(service: VectorDBService):
    """Test removing vectors from the index."""
    print("\n" + "=" * 60)
    print("벡터 삭제 테스트")
    print("=" * 60)

    original_count = service.index.ntotal
    print(f"삭제 전 벡터 수: {original_count}")

    # Remove vectors with index 0 and 1
    removed = service.remove_vectors([0, 1])

    print(f"삭제된 벡터 수: {removed}")
    print(f"삭제 후 벡터 수: {service.index.ntotal}")

    assert service.index.ntotal == original_count - removed

    print("\n✅ 벡터 삭제 테스트 완료!")


def test_clear(service: VectorDBService):
    """Test clearing the index."""
    print("\n" + "=" * 60)
    print("인덱스 초기화 테스트")
    print("=" * 60)

    service.clear()

    stats = service.get_stats()
    print(f"초기화 후 통계: {stats}")

    assert stats["initialized"] is False
    assert stats["total_vectors"] == 0

    print("\n✅ 인덱스 초기화 테스트 완료!")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Knowledge Base AI Chatbot - FAISS 벡터 DB 테스트")
    print("=" * 60)

    # Test create index
    service = test_create_index()

    # Test add vectors
    vectors = test_add_vectors(service)

    # Test search
    test_search(service, vectors)

    # Test save/load
    test_save_load(service)

    # Test remove vectors
    test_remove_vectors(service)

    # Test clear
    test_clear(service)

    print("\n" + "=" * 60)
    print("모든 FAISS 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
