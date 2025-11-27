#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Qdrant Memory System Verification Script.

This script verifies that the Qdrant vector database and memory system
are working correctly. It tests:

1. ✅ Qdrant connectivity
2. ✅ Collection creation/existence
3. ✅ Memory storage (with and without session_id)
4. ✅ Memory retrieval (semantic search)
5. ✅ Duplicate detection
6. ✅ Session isolation (multi-user safety)
7. ✅ Configuration validation

Usage:
    python verify_qdrant.py

Exit codes:
    0: All tests passed
    1: One or more tests failed
"""

import sys
import uuid
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, "src")

from ai_companion.modules.memory.long_term.constants import (
    DUPLICATE_DETECTION_SIMILARITY_THRESHOLD,
    ENABLE_SESSION_ISOLATION,
    QDRANT_COLLECTION_NAME,
)
from ai_companion.modules.memory.long_term.startup import initialize_memory_system, verify_memory_system
from ai_companion.modules.memory.long_term.vector_store import get_vector_store


def print_header(text: str) -> None:
    """Print a formatted test section header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}")


def print_test(test_name: str, passed: bool, details: str = "") -> None:
    """Print test result with status indicator."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"       {details}")


def run_tests() -> bool:
    """Run all verification tests. Returns True if all pass."""
    all_passed = True

    # TEST 1: Initialization
    print_header("TEST 1: System Initialization")
    try:
        success = initialize_memory_system(required=False)
        print_test("Initialize memory system", success)
        all_passed = all_passed and success
        if not success:
            print("\n⚠️ Memory system initialization failed. Check Qdrant connection.")
            return False
    except Exception as e:
        print_test("Initialize memory system", False, str(e))
        return False

    # TEST 2: Configuration
    print_header("TEST 2: Configuration Validation")
    try:
        print(f"  📋 Collection name: {QDRANT_COLLECTION_NAME}")
        print(f"  🔒 Session isolation: {'Enabled' if ENABLE_SESSION_ISOLATION else 'Disabled'}")
        print(f"  ♻️  Duplicate threshold: {DUPLICATE_DETECTION_SIMILARITY_THRESHOLD}")
        print_test("Configuration loaded", True)
    except Exception as e:
        print_test("Configuration loaded", False, str(e))
        all_passed = False

    # TEST 3: Collection Status
    print_header("TEST 3: Collection Status")
    try:
        status = verify_memory_system()
        if status:
            print(f"  📊 Status: {status['status']}")
            print(f"  📦 Collection: {status['collection']}")
            print(f"  💾 Memory count: {status['memory_count']}")
            print(f"  🟢 Health: {status['collection_status']}")
            print_test("Collection status check", True)
        else:
            print_test("Collection status check", False, "Status unavailable")
            all_passed = False
    except Exception as e:
        print_test("Collection status check", False, str(e))
        all_passed = False

    # Get vector store for remaining tests
    try:
        vector_store = get_vector_store()
    except Exception as e:
        print(f"\n❌ Failed to get VectorStore: {e}")
        return False

    # TEST 4: Memory Storage
    print_header("TEST 4: Memory Storage")
    test_memories = [
        ("User loves hiking in the mountains", "user_alice"),
        ("User prefers tea over coffee", "user_alice"),
        ("User is allergic to peanuts", "user_bob"),
    ]

    for text, session_id in test_memories:
        try:
            metadata = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
            }
            vector_store.store_memory(text, metadata, session_id=session_id)
            print_test(f"Store memory (session={session_id})", True, f"'{text[:40]}...'")
        except Exception as e:
            print_test(f"Store memory (session={session_id})", False, str(e))
            all_passed = False

    # TEST 5: Memory Retrieval
    print_header("TEST 5: Memory Retrieval (Semantic Search)")
    test_queries = [
        ("outdoor activities", "user_alice", ["hiking"]),
        ("beverage preferences", "user_alice", ["tea", "coffee"]),
        ("food allergies", "user_bob", ["peanuts"]),
    ]

    for query, session_id, expected_keywords in test_queries:
        try:
            results = vector_store.search_memories(query, k=3, session_id=session_id)
            found_keywords = any(
                any(keyword in result.text.lower() for keyword in expected_keywords) for result in results
            )
            print_test(f"Search '{query}' (session={session_id})", found_keywords, f"Found {len(results)} memories")
            if results:
                for i, result in enumerate(results, 1):
                    print(f"       {i}. '{result.text[:50]}...' (score: {result.score:.3f})")
            all_passed = all_passed and found_keywords
        except Exception as e:
            print_test(f"Search '{query}'", False, str(e))
            all_passed = False

    # TEST 6: Duplicate Detection
    print_header("TEST 6: Duplicate Detection")
    try:
        # Try to store a very similar memory
        duplicate_text = "User loves hiking in mountains"  # Very similar to first test memory
        similar = vector_store.find_similar_memory(duplicate_text, session_id="user_alice")

        if similar and similar.score and similar.score >= DUPLICATE_DETECTION_SIMILARITY_THRESHOLD:
            print_test("Duplicate detection", True, f"Found similar memory (score: {similar.score:.3f})")
        else:
            print_test("Duplicate detection", False, "Should have detected duplicate")
            all_passed = False
    except Exception as e:
        print_test("Duplicate detection", False, str(e))
        all_passed = False

    # TEST 7: Session Isolation
    print_header("TEST 7: Session Isolation")
    if ENABLE_SESSION_ISOLATION:
        try:
            # Alice's memories should not appear in Bob's search
            alice_results = vector_store.search_memories("hiking", k=5, session_id="user_alice")
            bob_results = vector_store.search_memories("hiking", k=5, session_id="user_bob")

            alice_has_hiking = any("hiking" in r.text.lower() for r in alice_results)
            bob_has_no_hiking = not any("hiking" in r.text.lower() for r in bob_results)

            isolated = alice_has_hiking and bob_has_no_hiking

            print_test(
                "Session isolation (Alice has hiking, Bob doesn't)",
                isolated,
                f"Alice: {len(alice_results)} results, Bob: {len(bob_results)} results",
            )
            all_passed = all_passed and isolated
        except Exception as e:
            print_test("Session isolation", False, str(e))
            all_passed = False
    else:
        print_test("Session isolation", True, "Skipped (ENABLE_SESSION_ISOLATION=False)")

    # TEST 8: Collection Info
    print_header("TEST 8: Collection Information")
    try:
        info = vector_store.get_collection_info()
        if info:
            print(f"  📊 Collection: {info['name']}")
            print(f"  💾 Total memories: {info['points_count']}")
            print(f"  🔢 Vectors: {info['vectors_count']}")
            print(f"  🟢 Status: {info['status']}")
            print_test("Get collection info", True)
        else:
            print_test("Get collection info", False, "Info unavailable")
            all_passed = False
    except Exception as e:
        print_test("Get collection info", False, str(e))
        all_passed = False

    return all_passed


def main() -> int:
    """Main entry point. Returns exit code."""
    # Set UTF-8 encoding for Windows console
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    print("\n" + "=" * 70)
    print("  QDRANT MEMORY SYSTEM VERIFICATION")
    print("=" * 70)
    print("\n🔍 Running comprehensive tests...\n")

    try:
        all_passed = run_tests()

        # Final summary
        print("\n" + "=" * 70)
        if all_passed:
            print("  ✅ ALL TESTS PASSED")
            print("=" * 70)
            print("\n🎉 Qdrant memory system is working correctly!")
            print("\nNext steps:")
            print("  1. ✅ Qdrant is configured and working")
            print("  2. ✅ Memory storage and retrieval functional")
            print(
                "  3. ✅ Session isolation is active"
                if ENABLE_SESSION_ISOLATION
                else "  3. ⚠️  Session isolation disabled (single-user mode)"
            )
            print("  4. ✅ Duplicate detection is working")
            print("\nYou're ready to use the memory system! 🚀")
            return 0
        else:
            print("  ❌ SOME TESTS FAILED")
            print("=" * 70)
            print("\n⚠️  Please review the failures above and:")
            print("  1. Check Qdrant is running: docker ps | findstr qdrant")
            print("  2. Verify .env configuration (QDRANT_URL, QDRANT_API_KEY)")
            print("  3. Check logs for detailed error messages")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
