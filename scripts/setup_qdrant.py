#!/usr/bin/env python3
"""
Setup Qdrant Vector Database

This script sets up Qdrant and tests the vector database integration.
"""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def setup_qdrant():
    """Set up and test Qdrant integration."""
    print("🔧 Setting up Qdrant Vector Database...")

    # Check if Qdrant is configured
    qdrant_url = os.getenv("QDRANT_URL", "")
    if not qdrant_url or "403" in qdrant_url or "cloud.qdrant" in qdrant_url:
        print("⚠️  Using local memory mode for Qdrant")
        os.environ["QDRANT_URL"] = ":memory:"

    try:
        from qdrant_client import QdrantClient

        # Test connection
        client = QdrantClient(url=os.getenv("QDRANT_URL"))
        collections = client.get_collections()
        print("✅ Qdrant connected successfully")
        print(f"📊 Existing collections: {len(collections.collections)}")

        # Test vector storage
        from memory.vector_store import VectorStore

        VectorStore()
        print("✅ Vector store initialized")

        # Test embeddings
        from memory.embeddings import embed

        test_text = ["This is a test sentence for embedding"]
        embeddings = embed(test_text)
        print(f"✅ Embeddings working: {len(embeddings)} vectors")

        return True

    except Exception as e:
        print(f"❌ Qdrant setup failed: {e}")
        return False


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    success = setup_qdrant()
    if success:
        print("🎉 Qdrant vector database ready!")
    else:
        print("⚠️  Qdrant unavailable - proceeding without vector features")
