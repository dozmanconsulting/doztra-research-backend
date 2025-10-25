import os
from pymilvus import connections, utility

uri = os.getenv("MILVUS_URI")
token = os.getenv("MILVUS_TOKEN")
db_name = os.getenv("MILVUS_DB_NAME") or "default"
print("Attempting Milvus connect...\nURI:", uri, "\nDB:", db_name, "\nToken len:", len(token) if token else 0)

try:
    if not uri:
        raise SystemExit("MILVUS_URI not set")
    connections.connect(alias="default", uri=uri, token=token, db_name=db_name)
    print("Connected. Server version:", utility.get_server_version())
    print("Databases:", utility.list_databases())
except Exception as e:
    print("Milvus connect error:", repr(e))
    raise
