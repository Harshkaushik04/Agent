import uuid
import json
import os
from rag_functions import dbConnect,split_documents,ingest_documents,load_embedding_model
from dotenv import load_dotenv

def make_rag_database(file_path: str) -> str:
    """
    Ingests a specific file into a unique RAG database (MongoDB + ChromaDB).
    Returns a JSON string containing the unique collection names needed to query it.
    """
    
    # 1. Validate Input
    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})

    # 2. Generate Unique Identifiers for this Database instance
    unique_id = uuid.uuid4().hex[:8]
    unique_collection_name = f"rag_collection_{unique_id}"
    
    print(f"    [INFO] Creating RAG Database for {os.path.basename(file_path)}")
    print(f"    [INFO] ID: {unique_collection_name}")

    # 3. Load & Split Document
    # Determine file type based on extension
    if file_path.lower().endswith(".pdf"):
        # We need to create a temporary directory logic or just pass the file path
        # Since DirectoryLoader expects a directory, we use PyMuPDFLoader directly for single file
        loader = PyMuPDFLoader(file_path)
        dir_content = loader.load()
    else:
        # Default to TextLoader for everything else
        loader = TextLoader(file_path, encoding='utf-8')
        dir_content = loader.load()

    docs = split_documents(dir_content=dir_content,
                           chunk_size=1000,
                           chunk_overlap=200)

    # 4. Connect to DB (Using the unique collection name)
    # We use the same Mongo DB but a NEW Collection
    mongo_collection, chroma_collection = dbConnect(
        mongo_url=mongo_url,
        chroma_host=chroma_host,
        chroma_port=chroma_port,
        mongo_database_name=mongo_database_name, 
        mongo_collection_name=unique_collection_name, # <--- UNIQUE
        chroma_collection_name=unique_collection_name # <--- UNIQUE
    )

    # 5. Load Embedding Model
    embedding_model = load_embedding_model(
        model_path=embedding_model_path,
        processor=Processor.GPU, # Or CPU depending on your hardware
        n_ctx=embed_n_ctx,
        n_batch=embed_n_batch
    )

    # 6. Ingest Data
    try:
        ingest_documents(
            docs=docs,
            mongo_collection=mongo_collection,
            chroma_collection=chroma_collection,
            embedding_model=embedding_model
        )
    except Exception as e:
        unload_embedding_model(embedding_model)
        return json.dumps({"error": str(e)})

    # 7. Cleanup
    unload_embedding_model(embedding_model)

    # 8. Return Connection Info
    # The "database_path" here is actually the config needed to connect to it.
    output_config = {
        "status": "success",
        "file_path": file_path,
        "mongo_collection": unique_collection_name,
        "chroma_collection": unique_collection_name,
        "mongo_db": mongo_database_name
    }

    return json.dumps(output_config)