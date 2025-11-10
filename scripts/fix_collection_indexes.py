#!/usr/bin/env python3
"""
Utility script to ensure all Qdrant collections have the required payload indexes.

This script can be used to fix existing collections that were created before
the indexing feature was added.

NOTE: The query_collection method now automatically detects and fixes missing
indexes when a query fails due to missing indexes. This script is provided for
manually fixing collections without needing to query them first.

Usage:
    # Activate virtual environment first (if using one)
    source venv/bin/activate  # or activate your environment

    # Fix a specific collection
    python scripts/fix_collection_indexes.py "Law's of Motion"

    # Fix all collections
    python scripts/fix_collection_indexes.py

If collection_name is provided, only that collection will be fixed.
Otherwise, all collections will be processed.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.repositories.qdrant_repository import QdrantRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_collection(repo: QdrantRepository, collection_name: str) -> bool:
    """
    Ensure indexes exist on a specific collection.

    Args:
        repo: QdrantRepository instance
        collection_name: Name of the collection to fix

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Processing collection: {collection_name}")

    if not repo.collection_exists(collection_name):
        logger.error(f"Collection '{collection_name}' does not exist")
        return False

    success = repo.ensure_indexes(collection_name)
    if success:
        logger.info(f"✓ Successfully ensured indexes on collection '{collection_name}'")
    else:
        logger.error(f"✗ Failed to ensure indexes on collection '{collection_name}'")

    return success


def fix_all_collections(repo: QdrantRepository) -> None:
    """
    Ensure indexes exist on all collections.

    Args:
        repo: QdrantRepository instance
    """
    collections = repo.list_collections()

    if not collections:
        logger.info("No collections found")
        return

    logger.info(f"Found {len(collections)} collection(s): {collections}")

    success_count = 0
    fail_count = 0

    for collection_name in collections:
        if fix_collection(repo, collection_name):
            success_count += 1
        else:
            fail_count += 1

    logger.info(f"\nSummary: {success_count} succeeded, {fail_count} failed")


def main():
    """Main entry point."""
    repo = QdrantRepository()

    if len(sys.argv) > 1:
        # Fix specific collection
        collection_name = sys.argv[1]
        logger.info(f"Fixing specific collection: {collection_name}")
        success = fix_collection(repo, collection_name)
        sys.exit(0 if success else 1)
    else:
        # Fix all collections
        logger.info("Fixing all collections")
        fix_all_collections(repo)


if __name__ == "__main__":
    main()
