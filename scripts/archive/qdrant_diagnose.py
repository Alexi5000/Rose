#!/usr/bin/env python3
"""Non-destructive Qdrant diagnostic script for Rose.

This script performs comprehensive diagnostics on the Qdrant collection:
- Gathers collection metadata and statistics
- Tests safe scroll operations to identify corrupted segments
- Lists suspicious point IDs
- Provides recommendations for fixes

All operations are READ-ONLY and non-destructive.

Usage:
    python scripts/qdrant_diagnose.py

Requirements:
    - Qdrant server must be running
    - QDRANT_URL environment variable or default http://localhost:6333
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from qdrant_client import QdrantClient
from qdrant_client.http import exceptions as qdrant_exceptions

from ai_companion.modules.memory.long_term.constants import QDRANT_COLLECTION_NAME
from ai_companion.settings import settings


class QdrantDiagnostics:
    """Non-destructive Qdrant diagnostics runner."""

    def __init__(self):
        """Initialize diagnostics with Qdrant client."""
        print(f"🔍 Initializing Qdrant diagnostics...")
        print(f"   URL: {settings.QDRANT_URL}")
        print(f"   Collection: {QDRANT_COLLECTION_NAME}\n")

        # Initialize client
        if settings.QDRANT_API_KEY and settings.QDRANT_API_KEY.lower() not in ["none", "", "null"]:
            self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        else:
            self.client = QdrantClient(url=settings.QDRANT_URL)

        self.collection_name = QDRANT_COLLECTION_NAME
        self.suspicious_points: List[str] = []
        self.errors: List[Dict[str, Any]] = []

    def check_connection(self) -> bool:
        """Check if Qdrant is reachable."""
        print("=" * 80)
        print("1. CONNECTION TEST")
        print("=" * 80)
        try:
            collections = self.client.get_collections()
            print(f"✅ Connection successful")
            print(f"   Total collections: {len(collections.collections)}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {type(e).__name__}: {str(e)}")
            self.errors.append({"test": "connection", "error": str(e), "type": type(e).__name__})
            return False

    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get detailed collection information."""
        print("\n" + "=" * 80)
        print("2. COLLECTION INFORMATION")
        print("=" * 80)
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)

            if not collection_exists:
                print(f"❌ Collection '{self.collection_name}' does not exist")
                print(f"   Available collections: {[col.name for col in collections.collections]}")
                return None

            # Get collection details
            info = self.client.get_collection(collection_name=self.collection_name)

            print(f"✅ Collection '{self.collection_name}' found")
            print(f"   Points count: {info.points_count}")
            print(f"   Vectors count: {info.vectors_count}")
            print(f"   Status: {info.status}")
            print(f"   Optimizer status: {info.optimizer_status if hasattr(info, 'optimizer_status') else 'N/A'}")

            # Extract vector configuration
            try:
                if hasattr(info, 'config') and hasattr(info.config, 'params'):
                    vectors_conf = getattr(info.config.params, 'vectors', None)
                    if vectors_conf:
                        print(f"   Vector size: {vectors_conf.size if hasattr(vectors_conf, 'size') else 'Unknown'}")
                        print(f"   Distance metric: {vectors_conf.distance if hasattr(vectors_conf, 'distance') else 'Unknown'}")
            except Exception:
                print(f"   Vector configuration: Unable to extract")

            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": str(info.status),
            }

        except Exception as e:
            print(f"❌ Failed to get collection info: {type(e).__name__}: {str(e)}")
            self.errors.append({"test": "collection_info", "error": str(e), "type": type(e).__name__})
            return None

    def test_scroll_operations(self, batch_size: int = 10, max_batches: int = 5) -> bool:
        """Test scroll operations to identify corrupted segments."""
        print("\n" + "=" * 80)
        print("3. SCROLL OPERATIONS TEST")
        print("=" * 80)
        print(f"   Testing scroll with batch_size={batch_size}, max_batches={max_batches}\n")

        try:
            offset = None
            batch_num = 0
            total_scrolled = 0
            corrupted_points = []

            while batch_num < max_batches:
                try:
                    # Attempt to scroll
                    records, next_offset = self.client.scroll(
                        collection_name=self.collection_name,
                        limit=batch_size,
                        offset=offset,
                        with_payload=True,
                        with_vectors=False,  # Skip vectors for faster scrolling
                    )

                    batch_num += 1
                    total_scrolled += len(records)

                    print(f"   ✅ Batch {batch_num}: Retrieved {len(records)} points")

                    # Check for suspicious payloads
                    for record in records:
                        point_id = record.id
                        payload = record.payload or {}

                        # Check for missing required fields
                        if "text" not in payload:
                            corrupted_points.append((point_id, "missing_text_field"))
                            print(f"      ⚠️ Point {point_id}: Missing 'text' field")

                        # Check for empty text
                        elif not payload.get("text"):
                            corrupted_points.append((point_id, "empty_text"))
                            print(f"      ⚠️ Point {point_id}: Empty text")

                        # Check for missing metadata
                        elif "timestamp" not in payload:
                            corrupted_points.append((point_id, "missing_timestamp"))
                            print(f"      ⚠️ Point {point_id}: Missing timestamp")

                    # Check if we're done
                    if next_offset is None:
                        print(f"\n   ✅ Scroll complete: Processed {total_scrolled} total points")
                        break

                    offset = next_offset

                except qdrant_exceptions.UnexpectedResponse as e:
                    print(f"\n   ❌ UnexpectedResponse at batch {batch_num + 1}")
                    print(f"      Error: {str(e)[:200]}")
                    print(f"      Status: {getattr(e, 'status_code', 'N/A')}")

                    self.errors.append({
                        "test": "scroll",
                        "batch": batch_num + 1,
                        "error": str(e)[:200],
                        "type": "UnexpectedResponse"
                    })

                    # Try to continue with next batch (skip corrupted segment)
                    print(f"      Attempting to skip corrupted segment...")
                    if offset is not None:
                        offset = str(int(offset) + batch_size) if isinstance(offset, (int, str)) and str(offset).isdigit() else None
                    batch_num += 1
                    continue

                except Exception as e:
                    print(f"\n   ❌ Unexpected error at batch {batch_num + 1}: {type(e).__name__}: {str(e)}")
                    self.errors.append({
                        "test": "scroll",
                        "batch": batch_num + 1,
                        "error": str(e),
                        "type": type(e).__name__
                    })
                    break

            # Summary
            if corrupted_points:
                print(f"\n   ⚠️ Found {len(corrupted_points)} suspicious points:")
                for point_id, issue in corrupted_points[:10]:  # Show first 10
                    print(f"      - {point_id}: {issue}")
                    self.suspicious_points.append(str(point_id))
                if len(corrupted_points) > 10:
                    print(f"      ... and {len(corrupted_points) - 10} more")

            return len(self.errors) == 0

        except Exception as e:
            print(f"❌ Scroll test failed: {type(e).__name__}: {str(e)}")
            self.errors.append({"test": "scroll", "error": str(e), "type": type(e).__name__})
            return False

    def test_search_operations(self) -> bool:
        """Test search operations to verify vector integrity."""
        print("\n" + "=" * 80)
        print("4. SEARCH OPERATIONS TEST")
        print("=" * 80)

        try:
            # Generate a test vector (384 dimensions for all-MiniLM-L6-v2)
            from sentence_transformers import SentenceTransformer

            print("   Loading embedding model...")
            model = SentenceTransformer("all-MiniLM-L6-v2")

            test_queries = [
                "test query about health",
                "user preferences",
                "conversation history",
            ]

            for query in test_queries:
                try:
                    print(f"\n   Testing search for: '{query}'")
                    embedding = model.encode(query)

                    results = self.client.search(
                        collection_name=self.collection_name,
                        query_vector=embedding.tolist(),
                        limit=3,
                    )

                    print(f"   ✅ Search successful: Found {len(results)} results")
                    for i, result in enumerate(results, 1):
                        print(f"      {i}. Score: {result.score:.3f}, ID: {result.id}")

                except qdrant_exceptions.UnexpectedResponse as e:
                    print(f"   ❌ Search failed: {type(e).__name__}")
                    print(f"      Error: {str(e)[:200]}")
                    self.errors.append({
                        "test": "search",
                        "query": query,
                        "error": str(e)[:200],
                        "type": "UnexpectedResponse"
                    })
                    return False

            return True

        except Exception as e:
            print(f"❌ Search test failed: {type(e).__name__}: {str(e)}")
            self.errors.append({"test": "search", "error": str(e), "type": type(e).__name__})
            return False

    def generate_report(self):
        """Generate diagnostic report with recommendations."""
        print("\n" + "=" * 80)
        print("5. DIAGNOSTIC REPORT")
        print("=" * 80)

        timestamp = datetime.now().isoformat()
        print(f"Report generated: {timestamp}\n")

        # Error summary
        if self.errors:
            print(f"❌ ERRORS DETECTED: {len(self.errors)}")
            print("-" * 80)
            for i, error in enumerate(self.errors, 1):
                print(f"\n{i}. {error.get('test', 'unknown').upper()} Test")
                print(f"   Type: {error.get('type', 'Unknown')}")
                print(f"   Error: {error.get('error', 'No details')[:200]}")
                if 'batch' in error:
                    print(f"   Batch: {error['batch']}")
        else:
            print("✅ NO ERRORS DETECTED")

        # Suspicious points
        if self.suspicious_points:
            print(f"\n⚠️ SUSPICIOUS POINTS: {len(self.suspicious_points)}")
            print("-" * 80)
            print(f"Point IDs with issues: {', '.join(self.suspicious_points[:20])}")
            if len(self.suspicious_points) > 20:
                print(f"... and {len(self.suspicious_points) - 20} more")

        # Recommendations
        print("\n" + "=" * 80)
        print("6. RECOMMENDATIONS")
        print("=" * 80)

        if self.errors or self.suspicious_points:
            print("\n🔧 RECOMMENDED ACTIONS:")
            print("\n1. **Backup Current Data**")
            print("   Run: python scripts/qdrant_backup.py")

            print("\n2. **Reindex Collection (Non-Destructive)**")
            print("   Run: python scripts/reindex_qdrant.py")
            print("   This will create a new collection and reindex valid points")

            print("\n3. **If Reindex Fails, Recreate Collection**")
            print("   ⚠️ WARNING: This will delete all memories!")
            print("   Run in Python:")
            print("   ```")
            print(f"   from qdrant_client import QdrantClient")
            print(f"   client = QdrantClient(url='{settings.QDRANT_URL}')")
            print(f"   client.delete_collection('{QDRANT_COLLECTION_NAME}')")
            print("   # Then restart Rose to recreate the collection")
            print("   ```")

            print("\n4. **Check Qdrant Server Logs**")
            print("   Run: docker logs qdrant")
            print("   Look for 'panic', 'segment', or 'corruption' messages")

        else:
            print("\n✅ ALL TESTS PASSED")
            print("   Your Qdrant collection appears healthy!")
            print("   No action required.")

        print("\n" + "=" * 80)


async def main():
    """Run all diagnostics."""
    print("\n" + "=" * 80)
    print("QDRANT DIAGNOSTICS FOR ROSE")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Qdrant URL: {settings.QDRANT_URL}")
    print(f"Collection: {QDRANT_COLLECTION_NAME}")
    print("=" * 80 + "\n")

    diagnostics = QdrantDiagnostics()

    # Run tests
    connected = diagnostics.check_connection()
    if not connected:
        print("\n❌ Cannot proceed without connection. Please check:")
        print("   1. Is Qdrant running? (docker ps | grep qdrant)")
        print("   2. Is QDRANT_URL correct in .env?")
        print("   3. Is there a firewall blocking port 6333?")
        return

    collection_info = diagnostics.get_collection_info()
    if not collection_info:
        print("\n❌ Collection not found. Has Rose been initialized?")
        return

    diagnostics.test_scroll_operations(batch_size=100, max_batches=50)
    diagnostics.test_search_operations()
    diagnostics.generate_report()

    print("\n" + "=" * 80)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
