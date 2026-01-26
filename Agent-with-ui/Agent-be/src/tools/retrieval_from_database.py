import os
import json
from bson.objectid import ObjectId
from pymongo import MongoClient
import chromadb
from tools.rag_functions import load_embedding_model, unload_embedding_model, create_query_vector, dbConnect, Processor
from dotenv import load_dotenv
from tools.model import clean_memory,load_model

load_dotenv("/home/harsh/RAG/Agent-with-ui/.env")
N_CTX=80000
# --- CONFIG ---
gen_model_path=os.getenv("DEEPSEEK_REASONING_MODEL_PATH")
mongo_url = os.getenv("MONGO_BASE_URL")
embedding_model_path = os.getenv("QWEN_EMBEDDING_MODEL_PATH")
chroma_host = os.getenv("CHROMA_HOST")
chroma_port = os.getenv("CHROMA_PORT")
embed_n_ctx = 8192 * 3
embed_n_batch = 512

def i_retrieval_from_database(
    gen_llm,
    database_details: dict,
    list_search_query_top_k: list[dict]
) -> list[dict]:
    """
    Retrieves relevant chunks from the RAG database for multiple queries.
    
    Args:
        database_details: {
            "mongo_database": str, 
            "mongo_collection": str, 
            "chroma_collection": str
        }
        list_search_query_top_k: List of { "search_query": str, "top_k": int }

    Returns:
        List of { "search_query": str, "retrieved_chunks": List[str] }
    """
    if gen_llm:
        try:
            clean_memory(gen_llm)
        except Exception as e:
            print(f"cant clean memory of gen_llm : {e}")
    results_output = []
    
    # 1. Connect to the Specific Database Collection
    try:
        mongo_collection, chroma_collection = dbConnect(
            mongo_url=mongo_url,
            chroma_host=chroma_host,
            chroma_port=chroma_port,
            mongo_database_name=database_details["mongo_database"],
            mongo_collection_name=database_details["mongo_collection"],
            chroma_collection_name=database_details["chroma_collection"]
        )
    except Exception as e:
        return [{"error": f"Database connection failed: {str(e)}"}]

    # 2. Load the Embedding Model (Once for all queries)
    # Note: If memory is tight, you might want to ensure this is unloaded in a 'finally' block.
    embedding_model = load_embedding_model(
        model_path=embedding_model_path,
        processor=Processor.GPU, # Use GPU if available
        n_ctx=embed_n_ctx,
        n_batch=embed_n_batch
    )

    try:
        # 3. Process Each Query
        for item in list_search_query_top_k:
            query_text = item["search_query"]
            top_k = item["top_k"]
            
            print(f"    [SEARCH] Querying: '{query_text}' (Top {top_k})")

            # A. Convert Query to Vector
            query_vec = create_query_vector(query_text, embedding_model)

            # B. Query ChromaDB for IDs
            chroma_results = chroma_collection.query(
                query_embeddings=[query_vec],
                n_results=top_k
            )
            
            # Chroma returns a list of lists (one per query). We only sent one.
            # ids = [['id1', 'id2', ...]]
            retrieved_ids_strs = chroma_results['ids'][0]
            
            # C. Fetch Content from MongoDB
            # Convert string IDs back to ObjectId for Mongo lookup
            retrieved_object_ids = [ObjectId(rid) for rid in retrieved_ids_strs]
            
            # Use $in operator to fetch all docs in one go
            cursor = mongo_collection.find({"_id": {"$in": retrieved_object_ids}})
            
            # Extract just the text content
            retrieved_chunks = []
            for doc in cursor:
                if "page_content" in doc:
                    retrieved_chunks.append(doc["page_content"])
            
            # D. Add to results
            results_output.append({
                "search_query": query_text,
                "retrieved_chunks": retrieved_chunks
            })

    except Exception as e:
        print(f"    [ERROR] Retrieval process failed: {e}")
        results_output.append({"error": str(e)})
        
    finally:
        # 4. cleanup: Unload model to free VRAM
        unload_embedding_model(embedding_model)
    load_model(gen_model_path,N_CTX)
    return results_output