"""
Test if Substrate's semantic components are installed correctly
"""

print("Testing Substrate Installation...")
print("="*60)

# Test 1: sentence-transformers
print("\n1. Testing sentence-transformers...")
try:
    from sentence_transformers import SentenceTransformer
    print("   ✅ sentence-transformers installed")

    # Try loading a small model
    print("   📥 Loading test model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("   ✅ Model loaded successfully")

    # Test embedding
    test_text = "This is a test of semantic understanding"
    embedding = model.encode(test_text)
    print(f"   ✅ Generated embedding: {len(embedding)} dimensions")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: ChromaDB
print("\n2. Testing ChromaDB...")
try:
    import chromadb
    print("   ✅ ChromaDB installed")

    # Try creating a client
    client = chromadb.Client()
    print("   ✅ ChromaDB client created")

    # Try creating a collection
    collection = client.get_or_create_collection("test")
    print("   ✅ Collection created")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Substrate semantic engine
print("\n3. Testing Substrate semantic engine...")
try:
    from substrate.cloud.matching.semantic_engine import SemanticMatcher
    print("   ✅ Semantic engine importable")

    matcher = SemanticMatcher()
    print("   ✅ Semantic matcher initialized")

except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("Installation test complete!")
print("\nIf all tests passed, you're ready to run:")
print("  python demo/substrate_semantic_demo.py")
