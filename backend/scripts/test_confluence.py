#!/usr/bin/env python3
"""Test script for Confluence API client.

Run from the backend directory:
    python scripts/test_confluence.py
"""

import json
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.services.confluence_client import ConfluenceClient


def test_confluence_connection():
    """Test Confluence connection and basic operations."""
    print("=" * 60)
    print("Confluence API Client Test")
    print("=" * 60)

    try:
        # Initialize client
        print("\n1. Initializing Confluence client...")
        client = ConfluenceClient()
        print("   ✓ Client initialized successfully")

        # Test connection
        print("\n2. Testing connection...")
        if client.test_connection():
            print("   ✓ Connection successful")
        else:
            print("   ✗ Connection failed")
            return False

        # Get all spaces
        print("\n3. Getting all spaces...")
        spaces = client.get_all_spaces()
        print(f"   ✓ Found {len(spaces)} spaces")
        for s in spaces[:5]:  # Show first 5
            print(f"      - {s['key']}: {s['name']} ({s['type']})")
        if len(spaces) > 5:
            print(f"      ... and {len(spaces) - 5} more")

        # Get recent pages
        print("\n4. Getting recent pages (last 5)...")
        pages = client.get_pages_updated_since(max_results=5)
        print(f"   ✓ Found {len(pages)} pages")

        # Format and display pages
        print("\n5. Formatting pages as documents...")
        for page in pages[:5]:
            doc = client.format_page_as_document(page)
            print(f"\n   Document: {doc['doc_id']}")
            print(f"   Title: {doc['title'][:60]}..." if len(doc['title']) > 60 else f"   Title: {doc['title']}")
            print(f"   Author: {doc['author']}")
            print(f"   URL: {doc['url']}")
            print(f"   Content length: {len(doc['content'])} chars")
            print(f"   Metadata: {json.dumps(doc['metadata'], indent=6)}")

        print("\n" + "=" * 60)
        print("All Confluence tests passed!")
        print("=" * 60)
        return True

    except ValueError as e:
        print(f"\n   ✗ Configuration error: {e}")
        print("\n   Please check your .env file and ensure:")
        print("   - CONFLUENCE_URL is set (e.g., https://your-domain.atlassian.net/wiki)")
        print("   - CONFLUENCE_EMAIL is set")
        print("   - CONFLUENCE_API_TOKEN is set")
        return False

    except Exception as e:
        print(f"\n   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_confluence_connection()
    sys.exit(0 if success else 1)
