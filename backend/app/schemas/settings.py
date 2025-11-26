"""Settings API schemas."""

from typing import Optional
from pydantic import BaseModel


class DataSourceConfig(BaseModel):
    """Data source connection configuration."""
    instance_type: str = "cloud"  # cloud or server
    url: str = ""
    token: str = ""
    enabled: bool = True


class DataSourcesResponse(BaseModel):
    """Data sources configuration response."""
    jira: DataSourceConfig
    confluence: DataSourceConfig


class DataSourceUpdateRequest(BaseModel):
    """Request to update a data source configuration."""
    instance_type: Optional[str] = None
    url: Optional[str] = None
    token: Optional[str] = None
    enabled: Optional[bool] = None


class ConnectionTestRequest(BaseModel):
    """Connection test request."""
    source: str  # jira or confluence
    url: str
    token: str


class ConnectionTestResponse(BaseModel):
    """Connection test response."""
    success: bool
    message: str
    details: Optional[str] = None
