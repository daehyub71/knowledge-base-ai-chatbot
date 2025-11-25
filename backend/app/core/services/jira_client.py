"""Jira API client using atlassian-python-api."""

import logging
from datetime import datetime
from typing import Any, Optional

from atlassian import Jira

from app.config import get_settings

logger = logging.getLogger(__name__)


class JiraClient:
    """Client for interacting with Jira API."""

    def __init__(self):
        """Initialize Jira client with settings from environment."""
        settings = get_settings()

        # Support both local server and cloud authentication
        username = settings.jira_username or settings.jira_email
        api_token = settings.jira_api_token
        password = settings.jira_password

        if not settings.jira_url:
            raise ValueError(
                "Jira configuration is incomplete. Please set JIRA_URL in .env"
            )

        if not api_token and not (username and password):
            raise ValueError(
                "Jira configuration is incomplete. "
                "Please set JIRA_API_TOKEN (for PAT) or JIRA_USERNAME and JIRA_PASSWORD in .env"
            )

        # Determine if using cloud or local server
        is_cloud = "atlassian.net" in (settings.jira_url or "")

        # Use Personal Access Token (PAT) if available, otherwise use username/password
        if api_token:
            # PAT authentication (Bearer token)
            self.jira = Jira(
                url=settings.jira_url,
                token=api_token,
                cloud=is_cloud,
            )
            logger.info(f"Jira client initialized with PAT for {settings.jira_url}")
        else:
            # Basic auth (username/password)
            self.jira = Jira(
                url=settings.jira_url,
                username=username,
                password=password,
                cloud=is_cloud,
            )
            logger.info(f"Jira client initialized with basic auth for {settings.jira_url}")

        self.base_url = settings.jira_url
        self.default_project_key = settings.jira_project_key

    def get_all_projects(self) -> list[dict[str, Any]]:
        """Get all accessible projects.

        Returns:
            List of project dictionaries with keys: key, name, id
        """
        try:
            projects = self.jira.projects()
            logger.info(f"Retrieved {len(projects)} projects from Jira")
            return [
                {
                    "key": p["key"],
                    "name": p["name"],
                    "id": p["id"],
                }
                for p in projects
            ]
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            raise

    def get_issues_updated_since(
        self,
        last_sync: Optional[datetime] = None,
        project_key: Optional[str] = None,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """Get issues updated since a given timestamp using JQL.

        Args:
            last_sync: Only get issues updated after this datetime
            project_key: Filter by project key (optional, uses default if not provided)
            max_results: Maximum number of results per request

        Returns:
            List of issue dictionaries
        """
        # Use default project key if not specified
        project_key = project_key or self.default_project_key

        # Build JQL query
        jql_parts = []

        if project_key:
            jql_parts.append(f'project = "{project_key}"')

        if last_sync:
            # Format datetime for JQL: "2024-01-15 10:30"
            formatted_date = last_sync.strftime("%Y-%m-%d %H:%M")
            jql_parts.append(f'updated >= "{formatted_date}"')

        jql = " AND ".join(jql_parts) if jql_parts else "ORDER BY updated DESC"
        if jql_parts:
            jql += " ORDER BY updated DESC"

        logger.info(f"Fetching issues with JQL: {jql}")

        try:
            all_issues = []
            start_at = 0

            while True:
                response = self.jira.jql(
                    jql,
                    start=start_at,
                    limit=max_results,
                    fields="summary,description,status,assignee,reporter,created,updated,comment",
                )

                issues = response.get("issues", [])
                if not issues:
                    break

                all_issues.extend(issues)
                start_at += len(issues)

                # Check if we've retrieved all issues
                if start_at >= response.get("total", 0):
                    break

            logger.info(f"Retrieved {len(all_issues)} issues from Jira")
            return all_issues

        except Exception as e:
            logger.error(f"Failed to get issues: {e}")
            raise

    def get_issue_details(self, issue_key: str) -> dict[str, Any]:
        """Get detailed information for a specific issue.

        Args:
            issue_key: The issue key (e.g., "PROJ-123")

        Returns:
            Issue dictionary with full details
        """
        try:
            issue = self.jira.issue(issue_key, expand="renderedFields")
            logger.debug(f"Retrieved details for issue {issue_key}")
            return issue
        except Exception as e:
            logger.error(f"Failed to get issue {issue_key}: {e}")
            raise

    def get_comments(self, issue_key: str) -> list[dict[str, Any]]:
        """Get all comments for a specific issue.

        Args:
            issue_key: The issue key (e.g., "PROJ-123")

        Returns:
            List of comment dictionaries
        """
        try:
            comments = self.jira.issue_get_comments(issue_key)
            comment_list = comments.get("comments", [])
            logger.debug(f"Retrieved {len(comment_list)} comments for issue {issue_key}")
            return comment_list
        except Exception as e:
            logger.error(f"Failed to get comments for {issue_key}: {e}")
            raise

    def format_issue_as_document(self, issue: dict[str, Any]) -> dict[str, Any]:
        """Format a Jira issue as a document for storage.

        Args:
            issue: Raw issue data from Jira API

        Returns:
            Formatted document dictionary
        """
        fields = issue.get("fields", {})
        issue_key = issue.get("key", "")

        # Build content from description and comments
        content_parts = []

        # Add summary
        summary = fields.get("summary", "")
        if summary:
            content_parts.append(f"# {summary}\n")

        # Add description
        description = fields.get("description", "")
        if description:
            content_parts.append(f"## Description\n{description}\n")

        # Add comments
        comments = fields.get("comment", {}).get("comments", [])
        if comments:
            content_parts.append("## Comments\n")
            for comment in comments:
                author = comment.get("author", {}).get("displayName", "Unknown")
                body = comment.get("body", "")
                created = comment.get("created", "")
                content_parts.append(f"**{author}** ({created}):\n{body}\n\n")

        content = "\n".join(content_parts)

        # Get author
        reporter = fields.get("reporter", {})
        author = reporter.get("displayName", "") if reporter else ""

        # Build URL
        url = f"{self.base_url}/browse/{issue_key}"

        # Get timestamps
        created_at = fields.get("created", "")
        updated_at = fields.get("updated", "")

        return {
            "doc_id": f"jira-{issue_key}",
            "doc_type": "jira",
            "title": f"[{issue_key}] {summary}",
            "url": url,
            "content": content,
            "author": author,
            "created_at": created_at,
            "updated_at": updated_at,
            "metadata": {
                "issue_key": issue_key,
                "project_key": issue_key.split("-")[0] if "-" in issue_key else "",
                "status": fields.get("status", {}).get("name", ""),
                "assignee": fields.get("assignee", {}).get("displayName", "") if fields.get("assignee") else "",
            },
        }

    def test_connection(self) -> bool:
        """Test the connection to Jira.

        Returns:
            True if connection is successful
        """
        try:
            # Try to get server info first (works for both cloud and local)
            server_info = self.jira.get_server_info()
            version = server_info.get("version", "Unknown")
            logger.info(f"Connected to Jira Server v{version}")
            return True
        except Exception as e:
            logger.error(f"Jira connection test failed: {type(e).__name__}: {e}")
            # Try alternative method - get projects list
            try:
                projects = self.jira.projects()
                logger.info(f"Connected to Jira (found {len(projects)} projects)")
                return True
            except Exception as e2:
                logger.error(f"Jira fallback test also failed: {type(e2).__name__}: {e2}")
                return False
