"""Settings API endpoints."""

import logging
import os
from typing import Dict

from fastapi import APIRouter, HTTPException

from app.schemas.settings import (
    DataSourceConfig,
    DataSourcesResponse,
    DataSourceUpdateRequest,
    ConnectionTestRequest,
    ConnectionTestResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])

# In-memory settings store (in production, use database or config file)
_settings_store: Dict[str, DataSourceConfig] = {
    "jira": DataSourceConfig(
        instance_type="cloud",
        url=os.getenv("JIRA_URL", ""),
        token=os.getenv("JIRA_API_TOKEN", ""),
        enabled=True,
    ),
    "confluence": DataSourceConfig(
        instance_type="cloud",
        url=os.getenv("CONFLUENCE_URL", ""),
        token=os.getenv("CONFLUENCE_API_TOKEN", ""),
        enabled=True,
    ),
}


@router.get("/data-sources", response_model=DataSourcesResponse)
async def get_data_sources() -> DataSourcesResponse:
    """Get current data source configurations.

    Returns the configuration for Jira and Confluence connections.
    Note: Tokens are masked for security.
    """
    # Return configs with masked tokens
    jira_config = _settings_store["jira"].model_copy()
    confluence_config = _settings_store["confluence"].model_copy()

    # Mask tokens (show only last 4 chars if exists)
    if jira_config.token:
        jira_config.token = "****" + jira_config.token[-4:] if len(jira_config.token) > 4 else "****"
    if confluence_config.token:
        confluence_config.token = "****" + confluence_config.token[-4:] if len(confluence_config.token) > 4 else "****"

    return DataSourcesResponse(
        jira=jira_config,
        confluence=confluence_config,
    )


@router.put("/data-sources/{source}")
async def update_data_source(
    source: str,
    request: DataSourceUpdateRequest,
) -> DataSourceConfig:
    """Update a data source configuration.

    Args:
        source: 'jira' or 'confluence'
        request: Configuration updates

    Returns:
        Updated configuration (with masked token)
    """
    if source not in ["jira", "confluence"]:
        raise HTTPException(status_code=400, detail="Invalid source. Use 'jira' or 'confluence'")

    current = _settings_store[source]

    # Update only provided fields
    if request.instance_type is not None:
        current.instance_type = request.instance_type
    if request.url is not None:
        current.url = request.url
    if request.token is not None:
        current.token = request.token
    if request.enabled is not None:
        current.enabled = request.enabled

    _settings_store[source] = current

    logger.info(f"Updated {source} configuration")

    # Return with masked token
    result = current.model_copy()
    if result.token:
        result.token = "****" + result.token[-4:] if len(result.token) > 4 else "****"

    return result


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_connection(request: ConnectionTestRequest) -> ConnectionTestResponse:
    """Test connection to a data source.

    Validates the provided credentials by attempting to connect
    to the Jira or Confluence API.
    """
    if request.source not in ["jira", "confluence"]:
        raise HTTPException(status_code=400, detail="Invalid source. Use 'jira' or 'confluence'")

    if not request.url:
        return ConnectionTestResponse(
            success=False,
            message="URL is required",
        )

    if not request.token:
        return ConnectionTestResponse(
            success=False,
            message="API token is required",
        )

    try:
        # TODO: Implement actual connection test
        # For now, just validate URL format and return mock success
        if not request.url.startswith("http"):
            return ConnectionTestResponse(
                success=False,
                message="Invalid URL format. URL must start with http:// or https://",
            )

        # Mock connection test (in production, make actual API call)
        import httpx

        # Build test URL
        if request.source == "jira":
            test_url = f"{request.url.rstrip('/')}/rest/api/2/myself"
        else:
            test_url = f"{request.url.rstrip('/')}/wiki/rest/api/user/current"

        # Try to connect (with short timeout)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                headers = {
                    "Authorization": f"Bearer {request.token}",
                    "Accept": "application/json",
                }
                response = await client.get(test_url, headers=headers)

                if response.status_code == 200:
                    return ConnectionTestResponse(
                        success=True,
                        message="Connection successful!",
                    )
                elif response.status_code == 401:
                    return ConnectionTestResponse(
                        success=False,
                        message="Authentication failed. Check your API token.",
                    )
                elif response.status_code == 403:
                    return ConnectionTestResponse(
                        success=False,
                        message="Access denied. Check your permissions.",
                    )
                else:
                    return ConnectionTestResponse(
                        success=False,
                        message=f"Connection failed with status {response.status_code}",
                    )
        except httpx.ConnectError:
            return ConnectionTestResponse(
                success=False,
                message="Could not connect to server. Check the URL.",
            )
        except httpx.TimeoutException:
            return ConnectionTestResponse(
                success=False,
                message="Connection timed out. Server may be unreachable.",
            )

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return ConnectionTestResponse(
            success=False,
            message=f"Connection test failed: {str(e)}",
        )
