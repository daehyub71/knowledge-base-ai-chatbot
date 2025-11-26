"""Global application state management.

This module holds global state that needs to be accessed across the application.
It's separated to avoid circular imports between main.py and API modules.
"""

from app.core.services.vector_db_service import VectorDBService

# Global services
vector_db_service: VectorDBService | None = None


def get_vector_db_service() -> VectorDBService | None:
    """Get the global VectorDBService instance.

    Returns:
        The VectorDBService instance or None if not initialized.
    """
    return vector_db_service


def set_vector_db_service(service: VectorDBService | None) -> None:
    """Set the global VectorDBService instance.

    Args:
        service: The VectorDBService instance to set.
    """
    global vector_db_service
    vector_db_service = service
