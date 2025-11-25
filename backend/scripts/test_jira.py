#!/usr/bin/env python3
"""Test script for Jira API client.

Run from the backend directory:
    python scripts/test_jira.py
"""

import json
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.services.jira_client import JiraClient


def test_jira_connection():
    """Test Jira connection and basic operations."""
    print("=" * 60)
    print("Jira API Client Test")
    print("=" * 60)

    try:
        # Initialize client
        print("\n1. Initializing Jira client...")
        client = JiraClient()
        print("   ✓ Client initialized successfully")

        # Test connection
        print("\n2. Testing connection...")
        if client.test_connection():
            print("   ✓ Connection successful")
        else:
            print("   ✗ Connection failed")
            return False

        # Get all projects
        print("\n3. Getting all projects...")
        projects = client.get_all_projects()
        print(f"   ✓ Found {len(projects)} projects")
        for p in projects[:5]:  # Show first 5
            print(f"      - {p['key']}: {p['name']}")
        if len(projects) > 5:
            print(f"      ... and {len(projects) - 5} more")

        # Get recent issues
        print("\n4. Getting recent issues (last 5)...")
        issues = client.get_issues_updated_since(max_results=5)
        print(f"   ✓ Found {len(issues)} issues")

        # Format and display issues
        print("\n5. Formatting issues as documents...")
        for issue in issues[:5]:
            doc = client.format_issue_as_document(issue)
            print(f"\n   Document: {doc['doc_id']}")
            print(f"   Title: {doc['title'][:60]}...")
            print(f"   Author: {doc['author']}")
            print(f"   URL: {doc['url']}")
            print(f"   Content length: {len(doc['content'])} chars")
            print(f"   Metadata: {json.dumps(doc['metadata'], indent=6)}")

        print("\n" + "=" * 60)
        print("All Jira tests passed!")
        print("=" * 60)
        return True

    except ValueError as e:
        print(f"\n   ✗ Configuration error: {e}")
        print("\n   Please check your .env file and ensure:")
        print("   - JIRA_URL is set (e.g., https://your-domain.atlassian.net)")
        print("   - JIRA_EMAIL is set")
        print("   - JIRA_API_TOKEN is set")
        return False

    except Exception as e:
        print(f"\n   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_jira_connection()
    sys.exit(0 if success else 1)
