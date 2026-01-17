import uuid
import json
import os
from tools.rag_functions import dbConnect, split_documents, ingest_documents, load_embedding_model, unload_embedding_model
from tools.model import clean_memory,load_model
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from enum import Enum, auto

load_dotenv("/home/harsh/RAG/Agent-with-ui/.env")
N_CTX=80000
# --- CONFIG ---
gen_model_path=os.getenv("DEEPSEEK_REASONING_MODEL_PATH")
mongo_url = os.getenv("MONGO_BASE_URL")
embedding_model_path = os.getenv("QWEN_EMBEDDING_MODEL_PATH")
chroma_host = os.getenv("CHROMA_HOST")
chroma_port = os.getenv("CHROMA_PORT")
mongo_database_name = os.getenv("MONGO_RAG_DATABASE_NAME")

embed_n_ctx = 8192 * 3
embed_n_batch = 512

class Processor(Enum):
    CPU = auto()
    GPU = auto()

def i_make_rag_database(gen_llm,file_paths: list[str]) -> str:
    """
    Ingests a list of files into a unique RAG database (MongoDB + ChromaDB).
    Returns a JSON string containing the unique collection names needed to query it.
    """
    if gen_llm:
        try:
            clean_memory(gen_llm)
        except Exception as e:
            print(f"cant clean memory from gen_llm: {e}")
    # 1. Generate Unique ID for this collective database
    unique_id = uuid.uuid4().hex[:8]
    unique_collection_name = f"rag_collection_{unique_id}"
    
    print(f"    [INFO] Creating RAG Database ID: {unique_collection_name}")
    print(f"    [INFO] Processing {len(file_paths)} files...")

    # 2. Load Content from All Files
    all_docs_content = []
    valid_files_processed = []

    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"    [WARN] Skipping missing file: {file_path}")
            continue
            
        try:
            if file_path.lower().endswith(".pdf"):
                loader = PyMuPDFLoader(file_path)
                file_docs = loader.load()
            else:
                loader = TextLoader(file_path, encoding='utf-8')
                file_docs = loader.load()
            
            all_docs_content.extend(file_docs)
            valid_files_processed.append(file_path)
            print(f"    [LOAD] Loaded: {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"    [ERROR] Failed to load {file_path}: {e}")

    if not all_docs_content:
        return json.dumps({"error": "No valid documents were loaded."})

    # 3. Split Documents
    docs = split_documents(dir_content=all_docs_content,
                           chunk_size=1000,
                           chunk_overlap=200)

    # 4. Connect to DB (Unique Collection)
    mongo_collection, chroma_collection = dbConnect(
        mongo_url=mongo_url,
        chroma_host=chroma_host,
        chroma_port=chroma_port,
        mongo_database_name=mongo_database_name, 
        mongo_collection_name=unique_collection_name, 
        chroma_collection_name=unique_collection_name
    )

    # 5. Load Embedding Model
    embedding_model = load_embedding_model(
        model_path=embedding_model_path,
        processor=Processor.GPU, 
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
        return json.dumps({"error": f"Ingestion failed: {str(e)}"})

    # 7. Cleanup
    unload_embedding_model(embedding_model)
    load_model(gen_model_path,N_CTX)

    # 8. Return Connection Info
    output_config = {
        "status": "success",
        "mongo_collection": unique_collection_name,
        "chroma_collection": unique_collection_name,
        "mongo_db": mongo_database_name,
        "files_ingested": valid_files_processed
    }

    return json.dumps(output_config)