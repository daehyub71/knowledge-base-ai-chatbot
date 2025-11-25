"""Confluence API client using atlassian-python-api."""

import logging
import re
from datetime import datetime
from typing import Any, Optional

from atlassian import Confluence

from app.config import get_settings

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Client for interacting with Confluence API."""

    def __init__(self):
        """Initialize Confluence client with settings from environment."""
        settings = get_settings()

        # Support both local server and cloud authentication
        username = settings.confluence_username or settings.confluence_email
        api_token = settings.confluence_api_token
        password = settings.confluence_password

        if not settings.confluence_url:
            raise ValueError(
                "Confluence configuration is incomplete. Please set CONFLUENCE_URL in .env"
            )

        if not api_token and not (username and password):
            raise ValueError(
                "Confluence configuration is incomplete. "
                "Please set CONFLUENCE_API_TOKEN (for PAT) or CONFLUENCE_USERNAME and CONFLUENCE_PASSWORD in .env"
            )

        # Determine if using cloud or local server
        is_cloud = "atlassian.net" in (settings.confluence_url or "")

        # Use Personal Access Token (PAT) if available, otherwise use username/password
        if api_token:
            # PAT authentication (Bearer token)
            self.confluence = Confluence(
                url=settings.confluence_url,
                token=api_token,
                cloud=is_cloud,
            )
            logger.info(f"Confluence client initialized with PAT for {settings.confluence_url}")
        else:
            # Basic auth (username/password)
            self.confluence = Confluence(
                url=settings.confluence_url,
                username=username,
                password=password,
                cloud=is_cloud,
            )
            logger.info(f"Confluence client initialized with basic auth for {settings.confluence_url}")

        self.base_url = settings.confluence_url
        self.default_space_key = settings.confluence_space_key

    def get_all_spaces(self) -> list[dict[str, Any]]:
        """Get all accessible spaces.

        Returns:
            List of space dictionaries with keys: key, name, id, type
        """
        try:
            spaces = []
            start = 0
            limit = 100

            while True:
                response = self.confluence.get_all_spaces(start=start, limit=limit)
                results = response.get("results", [])

                if not results:
                    break

                spaces.extend([
                    {
                        "key": s["key"],
                        "name": s["name"],
                        "id": s["id"],
                        "type": s.get("type", "global"),
                    }
                    for s in results
                ])

                start += len(results)
                if start >= response.get("size", 0):
                    break

            logger.info(f"Retrieved {len(spaces)} spaces from Confluence")
            return spaces

        except Exception as e:
            logger.error(f"Failed to get spaces: {e}")
            raise

    def get_pages_updated_since(
        self,
        last_sync: Optional[datetime] = None,
        space_key: Optional[str] = None,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """Get pages updated since a given timestamp using CQL.

        Args:
            last_sync: Only get pages updated after this datetime
            space_key: Filter by space key (optional, uses default if not provided)
            max_results: Maximum number of results per request

        Returns:
            List of page dictionaries
        """
        # Use default space key if not specified
        space_key = space_key or self.default_space_key

        # Build CQL query
        cql_parts = ["type = page"]

        if space_key:
            cql_parts.append(f'space = "{space_key}"')

        if last_sync:
            # Format datetime for CQL: "2024-01-15 10:30"
            formatted_date = last_sync.strftime("%Y-%m-%d %H:%M")
            cql_parts.append(f'lastModified >= "{formatted_date}"')

        cql = " AND ".join(cql_parts) + " ORDER BY lastModified DESC"

        logger.info(f"Fetching pages with CQL: {cql}")

        try:
            all_pages = []
            start = 0

            while True:
                response = self.confluence.cql(
                    cql,
                    start=start,
                    limit=max_results,
                    expand="version,body.storage",
                )

                results = response.get("results", [])
                if not results:
                    break

                all_pages.extend(results)
                start += len(results)

                # Check if we've retrieved all pages
                if start >= response.get("totalSize", 0):
                    break

            logger.info(f"Retrieved {len(all_pages)} pages from Confluence")
            return all_pages

        except Exception as e:
            logger.error(f"Failed to get pages: {e}")
            raise

    def get_page_content(self, page_id: str) -> dict[str, Any]:
        """Get full content for a specific page.

        Args:
            page_id: The page ID

        Returns:
            Page dictionary with full content
        """
        try:
            page = self.confluence.get_page_by_id(
                page_id,
                expand="body.storage,version,space,ancestors",
            )
            logger.debug(f"Retrieved content for page {page_id}")
            return page
        except Exception as e:
            logger.error(f"Failed to get page {page_id}: {e}")
            raise

    def get_page_comments(self, page_id: str) -> list[dict[str, Any]]:
        """Get all comments for a specific page.

        Args:
            page_id: The page ID

        Returns:
            List of comment dictionaries
        """
        try:
            comments = self.confluence.get_page_comments(
                page_id,
                expand="body.storage",
                depth="all",
            )
            comment_list = comments.get("results", [])
            logger.debug(f"Retrieved {len(comment_list)} comments for page {page_id}")
            return comment_list
        except Exception as e:
            logger.error(f"Failed to get comments for page {page_id}: {e}")
            raise

    @staticmethod
    def _html_to_text(html_content: str) -> str:
        """Convert HTML content to plain text.

        Args:
            html_content: HTML string

        Returns:
            Plain text string
        """
        if not html_content:
            return ""

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html_content)
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text

    def format_page_as_document(self, page: dict[str, Any]) -> dict[str, Any]:
        """Format a Confluence page as a document for storage.

        Args:
            page: Raw page data from Confluence API

        Returns:
            Formatted document dictionary
        """
        # Handle both CQL result format and direct page format
        if "content" in page:
            # CQL result format
            content_data = page.get("content", {})
            page_id = content_data.get("id", "")
            title = page.get("title", content_data.get("title", ""))
            body = content_data.get("body", {}).get("storage", {}).get("value", "")
            space = content_data.get("space", {})
            version = content_data.get("version", {})
        else:
            # Direct page format
            page_id = page.get("id", "")
            title = page.get("title", "")
            body = page.get("body", {}).get("storage", {}).get("value", "")
            space = page.get("space", {})
            version = page.get("version", {})

        # Convert HTML to text
        content = self._html_to_text(body)

        # Build content with title
        content_parts = [f"# {title}\n", content]

        # Get author from version
        author = ""
        if version:
            author = version.get("by", {}).get("displayName", "")

        # Build URL
        space_key = space.get("key", "")
        url = f"{self.base_url}/wiki/spaces/{space_key}/pages/{page_id}" if space_key else ""

        # Get timestamps
        created_at = page.get("history", {}).get("createdDate", "")
        updated_at = version.get("when", "") if version else ""

        # If using CQL result, try to get dates from lastModified
        if not updated_at and "lastModified" in page:
            updated_at = page.get("lastModified", "")

        return {
            "doc_id": f"confluence-{page_id}",
            "doc_type": "confluence",
            "title": title,
            "url": url,
            "content": "\n".join(content_parts),
            "author": author,
            "created_at": created_at,
            "updated_at": updated_at,
            "metadata": {
                "page_id": page_id,
                "space_key": space_key,
                "space_name": space.get("name", ""),
                "version": version.get("number", 1) if version else 1,
            },
        }

    def test_connection(self) -> bool:
        """Test the connection to Confluence.

        Returns:
            True if connection is successful
        """
        try:
            # Try to get spaces list to verify connection
            response = self.confluence.get_all_spaces(start=0, limit=1)
            space_count = response.get("size", 0)
            logger.info(f"Connected to Confluence successfully (found {space_count} spaces)")
            return True
        except Exception as e:
            logger.error(f"Confluence connection test failed: {e}")
            return False
