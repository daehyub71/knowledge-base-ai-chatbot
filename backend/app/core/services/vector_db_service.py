"""FAISS vector database service for similarity search."""

import logging
import pickle
from pathlib import Path
from typing import Any

import faiss
import numpy as np

logger = logging.getLogger(__name__)

# Default embedding dimension for text-embedding-3-large
DEFAULT_DIMENSION = 3072


class VectorDBService:
    """Service for managing FAISS vector index operations."""

    def __init__(self, dimension: int = DEFAULT_DIMENSION):
        """Initialize the vector database service.

        Args:
            dimension: Dimension of the embedding vectors
        """
        self.dimension = dimension
        self.index: faiss.IndexFlatL2 | None = None
        self.metadata: list[dict[str, Any]] = []
        self._index_path: Path | None = None
        self._metadata_path: Path | None = None

        logger.info(f"VectorDBService initialized with dimension={dimension}")

    def create_index(self, dimension: int | None = None) -> faiss.IndexFlatL2:
        """Create a new FAISS index.

        Args:
            dimension: Vector dimension (uses default if not specified)

        Returns:
            Created FAISS index
        """
        if dimension is not None:
            self.dimension = dimension

        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []

        logger.info(f"Created new FAISS IndexFlatL2 with dimension={self.dimension}")
        return self.index

    def add_vectors(
        self,
        vectors: list[list[float]] | np.ndarray,
        metadata: list[dict[str, Any]] | None = None,
    ) -> list[int]:
        """Add vectors to the index.

        Args:
            vectors: List of embedding vectors
            metadata: List of metadata dictionaries for each vector

        Returns:
            List of assigned index IDs
        """
        if self.index is None:
            self.create_index()

        # Convert to numpy array if needed
        if isinstance(vectors, list):
            vectors_array = np.array(vectors, dtype=np.float32)
        else:
            vectors_array = vectors.astype(np.float32)

        # Validate dimensions
        if vectors_array.shape[1] != self.dimension:
            raise ValueError(
                f"Vector dimension mismatch: expected {self.dimension}, "
                f"got {vectors_array.shape[1]}"
            )

        # Get starting index ID
        start_id = self.index.ntotal

        # Add vectors to index
        self.index.add(vectors_array)

        # Generate index IDs
        index_ids = list(range(start_id, start_id + len(vectors_array)))

        # Store metadata
        if metadata:
            if len(metadata) != len(vectors_array):
                raise ValueError(
                    f"Metadata count mismatch: {len(metadata)} metadata entries "
                    f"for {len(vectors_array)} vectors"
                )
            for i, meta in enumerate(metadata):
                meta_with_id = {**meta, "faiss_index_id": index_ids[i]}
                self.metadata.append(meta_with_id)
        else:
            # Add empty metadata entries
            for idx in index_ids:
                self.metadata.append({"faiss_index_id": idx})

        logger.info(
            f"Added {len(vectors_array)} vectors to index "
            f"(total: {self.index.ntotal})"
        )
        return index_ids

    def search(
        self,
        query_vector: list[float] | np.ndarray,
        k: int = 5,
    ) -> list[tuple[int, float, dict[str, Any]]]:
        """Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            k: Number of results to return

        Returns:
            List of (index_id, distance, metadata) tuples
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty or not initialized")
            return []

        # Convert to numpy array
        if isinstance(query_vector, list):
            query_array = np.array([query_vector], dtype=np.float32)
        else:
            query_array = query_vector.reshape(1, -1).astype(np.float32)

        # Validate dimension
        if query_array.shape[1] != self.dimension:
            raise ValueError(
                f"Query vector dimension mismatch: expected {self.dimension}, "
                f"got {query_array.shape[1]}"
            )

        # Limit k to available vectors
        k = min(k, self.index.ntotal)

        # Perform search
        distances, indices = self.index.search(query_array, k)

        # Build results
        results = []
        for i, (idx, dist) in enumerate(zip(indices[0], distances[0])):
            if idx == -1:  # FAISS returns -1 for not found
                continue

            # Get metadata if available
            meta = {}
            if idx < len(self.metadata):
                meta = self.metadata[idx]

            results.append((int(idx), float(dist), meta))

        logger.debug(f"Search returned {len(results)} results")
        return results

    def search_with_scores(
        self,
        query_vector: list[float] | np.ndarray,
        k: int = 5,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """Search and return results with similarity scores.

        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            score_threshold: Minimum similarity score (filters results)

        Returns:
            List of result dictionaries with score and metadata
        """
        results = self.search(query_vector, k)

        # Convert L2 distance to similarity score (0-1 range approximation)
        # Lower L2 distance = higher similarity
        scored_results = []
        for idx, distance, meta in results:
            # Convert distance to similarity (inverse relationship)
            # Using exponential decay for better score distribution
            similarity = 1.0 / (1.0 + distance)

            if score_threshold is not None and similarity < score_threshold:
                continue

            scored_results.append({
                "index_id": idx,
                "distance": distance,
                "similarity_score": similarity,
                "metadata": meta,
            })

        return scored_results

    def remove_vectors(self, index_ids: list[int]) -> int:
        """Remove vectors by their index IDs.

        Note: FAISS IndexFlatL2 doesn't support direct removal.
        This rebuilds the index without the specified vectors.

        Args:
            index_ids: List of index IDs to remove

        Returns:
            Number of vectors removed
        """
        if self.index is None or self.index.ntotal == 0:
            return 0

        ids_to_remove = set(index_ids)
        removed_count = 0

        # Get all vectors and metadata to keep
        keep_vectors = []
        keep_metadata = []

        for i in range(self.index.ntotal):
            if i in ids_to_remove:
                removed_count += 1
                continue

            # Reconstruct vector
            vector = self.index.reconstruct(i)
            keep_vectors.append(vector)

            if i < len(self.metadata):
                keep_metadata.append(self.metadata[i])

        # Rebuild index
        self.create_index()
        if keep_vectors:
            self.add_vectors(keep_vectors, keep_metadata)

        logger.info(f"Removed {removed_count} vectors from index")
        return removed_count

    def save_index(self, filepath: str | Path) -> None:
        """Save the FAISS index and metadata to files.

        Args:
            filepath: Path to save the index (metadata saved as .pkl)
        """
        if self.index is None:
            raise ValueError("No index to save")

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, str(filepath))
        self._index_path = filepath

        # Save metadata as pickle
        metadata_path = filepath.with_suffix(".pkl")
        with open(metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)
        self._metadata_path = metadata_path

        logger.info(
            f"Saved index ({self.index.ntotal} vectors) to {filepath} "
            f"and metadata to {metadata_path}"
        )

    def load_index(self, filepath: str | Path) -> faiss.IndexFlatL2:
        """Load a FAISS index and metadata from files.

        Args:
            filepath: Path to the index file

        Returns:
            Loaded FAISS index
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Index file not found: {filepath}")

        # Load FAISS index
        self.index = faiss.read_index(str(filepath))
        self.dimension = self.index.d
        self._index_path = filepath

        # Load metadata if exists
        metadata_path = filepath.with_suffix(".pkl")
        if metadata_path.exists():
            with open(metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
            self._metadata_path = metadata_path
        else:
            self.metadata = []
            logger.warning(f"Metadata file not found: {metadata_path}")

        logger.info(
            f"Loaded index ({self.index.ntotal} vectors) from {filepath}"
        )
        return self.index

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the current index.

        Returns:
            Dictionary with index statistics
        """
        if self.index is None:
            return {
                "initialized": False,
                "total_vectors": 0,
                "dimension": self.dimension,
                "metadata_count": 0,
            }

        return {
            "initialized": True,
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "metadata_count": len(self.metadata),
            "index_type": type(self.index).__name__,
            "index_path": str(self._index_path) if self._index_path else None,
        }

    def clear(self) -> None:
        """Clear the index and metadata."""
        self.index = None
        self.metadata = []
        self._index_path = None
        self._metadata_path = None
        logger.info("Cleared index and metadata")
