"""Test the HybridStore implementation."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage import HybridStore


def test_basic_functionality():
    """Test store and search functionality."""
    print("🧪 Testing HybridStore...\n")
    
    # Initialize store
    store = HybridStore()
    print("✅ HybridStore initialized")
    
    # Test store
    doc_id = store.store(
        content="Test company uses SaaS pricing model",
        metadata={"industry": "SaaS", "step": "discovery"},
        client_name="test_company"
    )
    print(f"✅ Stored document: {doc_id}")
    
    # Test search
    results = store.search("SaaS pricing", n_results=1)
    assert len(results) > 0, "Search should return results"
    print(f"✅ Search found {len(results)} results")
    
    # Test client list
    clients = store.get_all_clients()
    assert "test_company" in clients, "Client should be in list"
    print(f"✅ Found clients: {clients}")
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_basic_functionality()