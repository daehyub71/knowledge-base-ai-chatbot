"""Test script for OpenAI embedding service (bypassing Azure)."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from app.config import get_settings

settings = get_settings()

# Embedding model configuration
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSION = 3072


def test_openai_embedding():
    """Test OpenAI embedding directly."""
    print("=" * 60)
    print("OpenAI 임베딩 테스트 (Azure 우회)")
    print("=" * 60)

    if not settings.openai_api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        return

    # Initialize OpenAI client
    client = OpenAI(api_key=settings.openai_api_key)
    print(f"OpenAI 클라이언트 초기화 완료")
    print(f"모델: {EMBEDDING_MODEL}")
    print(f"예상 차원: {EMBEDDING_DIMENSION}")

    # Test texts
    test_texts = [
        "API 응답 시간 최적화",
        "데이터베이스 인덱스 튜닝",
        "Redis 캐싱 구현",
        "시스템 아키텍처 설계",
        "마이크로서비스 패턴",
    ]

    print(f"\n[단일 임베딩 테스트]")
    try:
        response = client.embeddings.create(
            input=test_texts[0],
            model=EMBEDDING_MODEL,
        )
        embedding = response.data[0].embedding
        print(f"✅ 단일 임베딩 생성 성공!")
        print(f"   텍스트: '{test_texts[0]}'")
        print(f"   벡터 차원: {len(embedding)}")
        print(f"   벡터 샘플 (처음 5개): {embedding[:5]}")
    except Exception as e:
        print(f"❌ 단일 임베딩 실패: {e}")
        return

    print(f"\n[배치 임베딩 테스트]")
    try:
        response = client.embeddings.create(
            input=test_texts,
            model=EMBEDDING_MODEL,
        )
        embeddings = [item.embedding for item in response.data]
        print(f"✅ 배치 임베딩 생성 성공!")
        print(f"   입력 텍스트 수: {len(test_texts)}")
        print(f"   생성된 임베딩 수: {len(embeddings)}")
        print(f"   각 벡터 차원: {len(embeddings[0])}")

        # Print each text and its embedding dimension
        for i, (text, emb) in enumerate(zip(test_texts, embeddings)):
            print(f"   {i+1}. '{text}' → {len(emb)} 차원")

    except Exception as e:
        print(f"❌ 배치 임베딩 실패: {e}")
        return

    print(f"\n[유사도 계산 테스트]")
    try:
        import numpy as np

        # Calculate cosine similarity between first two texts
        vec1 = np.array(embeddings[0])
        vec2 = np.array(embeddings[1])
        vec3 = np.array(embeddings[3])  # "시스템 아키텍처 설계"

        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        sim_1_2 = cosine_similarity(vec1, vec2)
        sim_1_4 = cosine_similarity(vec1, vec3)

        print(f"   '{test_texts[0]}' vs '{test_texts[1]}': {sim_1_2:.4f}")
        print(f"   '{test_texts[0]}' vs '{test_texts[3]}': {sim_1_4:.4f}")

    except Exception as e:
        print(f"❌ 유사도 계산 실패: {e}")

    print("\n" + "=" * 60)
    print("✅ 모든 OpenAI 임베딩 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    test_openai_embedding()
