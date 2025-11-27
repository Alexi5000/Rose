#!/usr/bin/env python3
"""Utility to inspect Qdrant collection and segment information.

This script queries the Qdrant HTTP API to return:
- list of collections
- collection information (config, vectors size)
- basic statistics: points_count, indexed_vectors_count, segments_count

Usage:
    python scripts/qdrant_inspect.py
"""

import os
import sys
import requests

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6335")
COLLECTION = os.environ.get("QDRANT_COLLECTION", "long_term_memory")


def list_collections():
    r = requests.get(f"{QDRANT_URL}/collections")
    r.raise_for_status()
    print("Collections:")
    print(r.text)


def collection_info():
    r = requests.get(f"{QDRANT_URL}/collections/{COLLECTION}")
    r.raise_for_status()
    print(f"Collection [{COLLECTION}] info:")
    print(r.text)


def list_points(limit: int = 5):
    r = requests.post(f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll", json={"limit": limit, "with_payload": True, "with_vector": True})
    try:
        r.raise_for_status()
    except Exception:
        print("Failed to list points:", r.status_code, r.text)
        return
    print(f"Sample points (limit={limit}):")
    print(r.text)


def main():
    try:
        list_collections()
        print("\n---\n")
        collection_info()
        print("\n---\n")
        list_points(5)
    except Exception as e:
        print("Error while gathering Qdrant info:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
