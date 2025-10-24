#!/usr/bin/env python3
"""
Quick test for Zilliz Cloud connection
Tests the specific cluster credentials provided
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_zilliz_connection():
    """Test connection to your specific Zilliz Cloud cluster"""
    print("🚀 Testing Zilliz Cloud Connection")
    print("=" * 40)
    
    # Get Zilliz Cloud credentials from environment
    host = os.getenv("MILVUS_HOST", "localhost")
    port = int(os.getenv("MILVUS_PORT", "19530"))
    user = os.getenv("MILVUS_USER")
    password = os.getenv("MILVUS_PASSWORD")
    use_secure = os.getenv("MILVUS_USE_SECURE", "false").lower() == "true"
    
    print(f"🔗 Connecting to: {host}")
    print(f"👤 User: {user or 'None'}")
    print(f"🔐 Password: {'*' * len(password) if password else 'None'}")
    print(f"🔒 Secure: {use_secure}")
    print()
    
    try:
        from pymilvus import connections, utility, Collection, FieldSchema, CollectionSchema, DataType
        
        print("📦 pymilvus library loaded successfully")
        
        # Connect to Zilliz Cloud or local Milvus
        print("🔌 Attempting connection...")
        connection_params = {
            "alias": "default",
            "host": host,
            "port": port
        }
        
        if user and password:
            connection_params["user"] = user
            connection_params["password"] = password
            
        if use_secure:
            connection_params["secure"] = True
            
        connections.connect(**connection_params)
        
        if connections.has_connection("default"):
            print("✅ Connected to Zilliz Cloud successfully!")
            
            # Test basic operations
            print("\n🧪 Testing basic operations...")
            
            # List existing collections
            collections = utility.list_collections()
            print(f"📚 Found {len(collections)} existing collections: {collections}")
            
            # Test creating a simple collection
            test_collection_name = "test_knowledge_base"
            
            # Check if test collection exists and drop it
            if utility.has_collection(test_collection_name):
                print(f"🗑️  Dropping existing test collection: {test_collection_name}")
                utility.drop_collection(test_collection_name)
            
            # Create a test collection schema
            print(f"🏗️  Creating test collection: {test_collection_name}")
            
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="content_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=1000)
            ]
            
            schema = CollectionSchema(fields, description="Test collection for Knowledge Base")
            collection = Collection(test_collection_name, schema)
            
            print("✅ Test collection created successfully!")
            
            # Create index
            print("🔍 Creating vector index...")
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index("embedding", index_params)
            print("✅ Vector index created successfully!")
            
            # Test inserting some dummy data
            print("📝 Testing data insertion...")
            import numpy as np
            
            test_data = [
                ["test_content_1", "test_content_2"],  # content_id
                [np.random.random(768).tolist(), np.random.random(768).tolist()],  # embedding
                ["This is test content 1", "This is test content 2"]  # text
            ]
            
            insert_result = collection.insert(test_data)
            print(f"✅ Inserted {len(insert_result.primary_keys)} records")
            
            # Load collection for search
            collection.load()
            print("✅ Collection loaded for search")
            
            # Test search
            print("🔍 Testing vector search...")
            search_vectors = [np.random.random(768).tolist()]
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            
            results = collection.search(
                search_vectors,
                "embedding",
                search_params,
                limit=2,
                output_fields=["content_id", "text"]
            )
            
            print(f"✅ Search completed! Found {len(results[0])} results")
            for i, result in enumerate(results[0]):
                print(f"   Result {i+1}: {result.entity.get('text')} (distance: {result.distance:.4f})")
            
            # Clean up test collection
            print("🧹 Cleaning up test collection...")
            utility.drop_collection(test_collection_name)
            print("✅ Test collection dropped")
            
            print("\n🎉 All tests passed! Your Zilliz Cloud cluster is ready for production!")
            
            return True
            
        else:
            print("❌ Failed to establish connection")
            return False
            
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install pymilvus")
        return False
        
    except Exception as e:
        print(f"❌ Connection or operation failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Check if your Zilliz Cloud cluster is running")
        print("   2. Verify the credentials are correct")
        print("   3. Ensure your IP is whitelisted (if applicable)")
        print("   4. Check your internet connection")
        return False
    
    finally:
        # Disconnect
        try:
            connections.disconnect("default")
            print("🔌 Disconnected from Zilliz Cloud")
        except:
            pass

def test_environment_variables():
    """Test if environment variables are set correctly"""
    print("\n🔧 Testing Environment Variables")
    print("=" * 35)
    
    env_vars = {
        "MILVUS_HOST": os.getenv("MILVUS_HOST"),
        "MILVUS_PORT": os.getenv("MILVUS_PORT"),
        "MILVUS_USER": os.getenv("MILVUS_USER"),
        "MILVUS_PASSWORD": os.getenv("MILVUS_PASSWORD"),
        "MILVUS_USE_SECURE": os.getenv("MILVUS_USE_SECURE")
    }
    
    all_set = True
    for var, value in env_vars.items():
        if value:
            masked_value = value if var != "MILVUS_PASSWORD" else "*" * len(value)
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"❌ {var}: Not set")
            all_set = False
    
    if all_set:
        print("✅ All environment variables are configured!")
    else:
        print("❌ Some environment variables are missing")
        print("   Copy .env.template to .env and update the values")
    
    return all_set

if __name__ == "__main__":
    print("🧪 Zilliz Cloud Connection Test")
    print("=" * 50)
    
    # Test environment variables first
    env_ok = test_environment_variables()
    
    # Test connection
    connection_ok = test_zilliz_connection()
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    print(f"Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Zilliz Connection:     {'✅ PASS' if connection_ok else '❌ FAIL'}")
    
    if env_ok and connection_ok:
        print("\n🎉 Your Zilliz Cloud setup is perfect!")
        print("   Ready for production deployment!")
    else:
        print("\n🔧 Setup needs attention")
        if not env_ok:
            print("   - Configure environment variables")
        if not connection_ok:
            print("   - Check Zilliz Cloud connection")
