import sys
import os
import gc
import torch
import chromadb
from pymongo import MongoClient
from bson.objectid import ObjectId
from llama_cpp import Llama
from langchain_community.document_loaders import TextLoader, DirectoryLoader, PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re,time
from enum import Enum,auto
from dotenv import load_dotenv
load_dotenv("../.env")
# ==========================================
# CONFIG & SETUP
# ==========================================

QUERY = "What is the different methods of data ingestion in rag and explain them in detail"

class FileType(Enum):
    PDF=auto()
    TXT=auto()
    SIMPLE_TEXT=auto()

class Processor(Enum):
    CPU=auto()
    GPU=auto()


def clean_memory(model):
    if model:
        model.close() 
        del model
    gc.collect()
    torch.cuda.empty_cache()   
    print("    [SYSTEM] Memory/VRAM Forcefully Cleared.")

def documents_loader(source,file_type):
    print(f"    [INFO] Scanning '{source}' for PDFs...")
    if file_type==FileType.PDF:
        dir_loader = DirectoryLoader(path=source, glob="**/*.pdf", loader_cls=PyMuPDFLoader)
        dir_content = dir_loader.load()
        print(f"    [INFO] Loaded {len(dir_content)} PDF pages.")
    elif file_type==FileType.TXT:
        dir_loader = DirectoryLoader(path=source, glob="**/*.txt", loader_cls=TextLoader)
        dir_content = dir_loader.load()
        print(f"    [INFO] Loaded {len(dir_content)} TXT pages.")
    elif file_type==FileType.SIMPLE_TEXT:
        print("    [INFO] Loading raw string content...")
        return [Document(page_content=source, metadata={"source": "manual_input"})]
    return dir_content

def split_documents(dir_content,chunk_size,chunk_overlap):
    print("    [INFO] Splitting documents...")
    text_splitter = RecursiveCharacterTextSplitter(separators=["\n","\n\n",""," "], chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter.split_documents(dir_content)
    print(f"    [SUCCESS] Created {len(docs)} chunks")
    return docs

def dbConnect(mongo_url,chroma_host,chroma_port,mongo_database_name,mongo_collection_name,chroma_collection_name):
    mongo_collection=MongoClient(mongo_url)[mongo_database_name][mongo_collection_name]
    chroma_client=chromadb.HttpClient(host=chroma_host,port=chroma_port)        
    chroma_collection=chroma_client.get_or_create_collection(chroma_collection_name)
    return mongo_collection,chroma_collection

def load_embedding_model(model_path,processor,n_ctx,n_batch):
    if(processor==Processor.CPU):
        embedding_model=Llama(model_path=model_path,
                          n_gpu_layers=0,
                          n_ctx=n_ctx,
                          n_batch=n_batch,
                          embedding=True,
                          verbose=False)
    else:
        embedding_model=Llama(model_path=model_path,
                          n_gpu_layers=-1,
                          n_ctx=n_ctx,
                          n_batch=n_batch,
                          embedding=True,
                          verbose=False)
    return embedding_model

def unload_embedding_model(model):
    clean_memory(model)

def ingest_documents(docs, mongo_collection, chroma_collection, embedding_model):
    total_number = len(docs)
    batch_size = 50  # Process 50 docs at a time
    print(f"    [INFO] Ingesting {total_number} chunks in batches of {batch_size}...")

    # Buffers for batching
    batch_mongo_docs = []
    batch_ids = []
    batch_embeddings = []
    batch_metadatas = []

    for i, doc in enumerate(docs):
        doc_oid = ObjectId()
        doc_id_str = str(doc_oid)
        mongo_doc = {
            "_id": doc_oid,
            "page_content": doc.page_content,
            "metadata": doc.metadata
        }
        vec_data = embedding_model.create_embedding(doc.page_content)
        if isinstance(vec_data, dict):
            vec = vec_data["data"][0]["embedding"]
        else:
            vec = vec_data
        if len(vec) > 0 and isinstance(vec[0], list):
            vec = vec[0]
        batch_mongo_docs.append(mongo_doc)
        batch_ids.append(doc_id_str)
        batch_embeddings.append(vec)
        batch_metadatas.append(doc.metadata)
        if len(batch_ids) >= batch_size:
            print(f"    [BATCH] processing {i+1}/{total_number}...", end='\r')
            mongo_collection.insert_many(batch_mongo_docs)
            chroma_collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas
            )
            batch_mongo_docs = []
            batch_ids = []
            batch_embeddings = []
            batch_metadatas = []
    if batch_ids:
        print(f"    [BATCH] processing {total_number}/{total_number}...", end='\r')
        mongo_collection.insert_many(batch_mongo_docs)
        chroma_collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings,
            metadatas=batch_metadatas
        )
    print(f"\n    [SUCCESS] Ingested {total_number} chunks.")

def create_query_vector(query, embedding_model):
    print(f"    [INFO] Embedding Query: '{query}'")
    full_query = "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: " + query
    query_vec_data = embedding_model.create_embedding(full_query)
    if isinstance(query_vec_data, dict):
        query_vec = query_vec_data["data"][0]["embedding"]
    else:
        query_vec = query_vec_data
    if len(query_vec) > 0 and isinstance(query_vec[0], list):
        query_vec = query_vec[0]
    return query_vec

def retrieve(mongo_collection,chroma_collection,query_vec,n_results):
    print("\n================ PHASE 5: RETRIEVAL ===============================")
    results = chroma_collection.query(query_embeddings=[query_vec], n_results=n_results)
    retrieved_ids = [ObjectId(i) for i in results['ids'][0]]
    mongo_docs = list(mongo_collection.find({"_id": {"$in": retrieved_ids}}))
    print(f"    [INFO] Retrieved {len(mongo_docs)} documents from MongoDB.")
    return mongo_docs

def load_gen_model(model_path,processor,n_ctx,n_batch):
    if(processor==Processor.CPU):
        gen_model=Llama(model_path=model_path,
                        n_gpu_layers=0,
                        n_ctx=n_ctx,
                        n_batch=n_batch,
                        verbose=False)
    else:
        gen_model=Llama(model_path=model_path,
                        n_gpu_layers=-1,
                        n_ctx=n_ctx,
                        n_batch=n_batch,
                        verbose=False)
    return gen_model

def unload_gen_model(model):
    clean_memory(model)

def re_ranking_via_gen_model(mongo_docs,query,gen_model,n_results):
    print(f"    [RERANK] Scoring {len(mongo_docs)} documents (0-10 scale)...")
    scored_docs = []

    for doc in mongo_docs:
        # Prompt the LLM to be a judge
        score_prompt = f"""<|im_start|>system
You are a relevance classifier.
Task: Rate how well the provided Text answers the User Query.
Scale:
0 = Completely unrelated (e.g., different topic, football, math).
5 = Related topic but does not contain the answer.
10 = Contains the exact answer.

Output format: Just the integer score (0-10).
<|im_end|>
<|im_start|>user
Query: {query}
Text: {doc['page_content']}
<|im_end|>
<|im_start|>assistant
"""
        try:
            # Generate a tiny response (just the number)
            output = gen_model(score_prompt, max_tokens=5, stop=["<|im_end|>"], temperature=0.1)
            text_out = output['choices'][0]['text']
            # Extract the first number found
            match = re.search(r"\d+", text_out)
            score = int(match.group()) if match else 0
        except:
            score = 0
        print("score prompt:",score_prompt)
        print(f"       - Doc ID ...{str(doc['_id'])[-n_results:]} | Score: {score}/10")
        scored_docs.append((score, doc))

    # 3. Sort and Slice (Top 3)
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    top_docs = [doc for score, doc in scored_docs[:n_results]]
    print(f"    [INFO] Selected top {len(top_docs)} most relevant docs.")
    return top_docs

def generation(gen_model,top_docs,query):
    print("\n================ PHASE 6: GENERATION ==============================")

    # Use 'top_5_docs' instead of 'mongo_docs'
    context_str = "\n".join([f"- {d.get('page_content', '')}" for d in top_docs])

    prompt = f"""<|im_start|>system
    You are a helpful research assistant. 
Your task is to answer the user's question using ONLY the provided documents.

GUIDELINES:
1. If the documents mention specific methods (e.g., DPR, Dense Retrieval), describe them and what the text says about their performance.
2. Do NOT use outside knowledge.
3. If the documents do not contain the answer, summarize what *is* discussed in the documents instead.
    Context:
    {context_str}<|im_end|>
    <|im_start|>user
    {query}<|im_end|>
    <|im_start|>assistant
    """

    print(f"\nprompt:{prompt}")
    print("\n--- AGENT THINKING ---")

    # Stream Generation
    stream = gen_model(
        prompt, 
        max_tokens=None, 
        stop=["<|im_end|>"], 
        stream=True, 
        temperature=0.6
    )

    for output in stream:
        token = output['choices'][0]['text']
        print(token, end='', flush=True)

    print("\n")
    print("================ DONE =====================")

def delete_mongo_collection(mongo_database,mongo_collection,mongo_url):
    mongo_database=MongoClient(mongo_url)[mongo_database]
    mongo_database.drop_collection(mongo_collection)
    print(f"[SUCCESS] Dropped collection {mongo_collection}")

def delete_chroma_collection(chroma_host,chroma_port,chroma_collection):
    chroma_client=chromadb.HttpClient(host=chroma_host,port=chroma_port)
    chroma_client.delete_collection(chroma_collection)
    print(f"[SUCCESS] Deleted collection {chroma_collection}")

def ingestion_retrieval_generation(flag,pdf_directory_path,text_directory_path,simple_text_var,mongo_url,
                                   mongo_database_name,mongo_collection_name,chroma_collection_name,
                                   chroma_host,chroma_port,embedding_model_path,gen_model_path,
                                   query,gen_n_ctx,gen_n_batch,embed_n_ctx,embed_n_batch,
                                   retrieve_n_results,re_rank_n_results):#flag=0 =>both pdf and text,flag=1=>only pdf,flag=2=>only text,flag=3=>simple text variable
    pdf_dir_content=[]
    text_dir_content=[]
    if flag==0 or flag==1:
        pdf_dir_content=documents_loader(source=pdf_directory_path,
                                        file_type=FileType.PDF)
    if flag==0 or flag==2:
        text_dir_content=documents_loader(source=text_directory_path,
                                    file_type=FileType.TXT)
    if flag==3:
        text_dir_content=documents_loader(source=simple_text_var,
                                          file_type=FileType.SIMPLE_TEXT)
    dir_content=pdf_dir_content+text_dir_content
    docs=split_documents(dir_content=dir_content,
                        chunk_size=1000,
                        chunk_overlap=400)
    mongo_collection,chroma_collection=dbConnect(mongo_url=mongo_url,
                                                chroma_host=chroma_host,
                                                chroma_port=chroma_port,
                                                mongo_database_name=mongo_database_name,
                                                mongo_collection_name=mongo_collection_name,
                                                chroma_collection_name=chroma_collection_name)
    embedding_model=load_embedding_model(model_path=embedding_model_path,
                                        processor=Processor.GPU,
                                        n_ctx=embed_n_ctx,
                                        n_batch=embed_n_batch)
    ingest_documents(docs=docs,
                    mongo_collection=mongo_collection,
                    chroma_collection=chroma_collection,
                    embedding_model=embedding_model)
    query_vec=create_query_vector(query=query,
                                embedding_model=embedding_model)
    unload_embedding_model(embedding_model)
    mongo_docs=retrieve(mongo_collection=mongo_collection,
                        chroma_collection=chroma_collection,
                        query_vec=query_vec,
                        n_results=retrieve_n_results)
    gen_model=load_gen_model(model_path=gen_model_path,
                            processor=Processor.GPU,
                            n_ctx=gen_n_ctx,
                            n_batch=gen_n_batch)
    top_docs=re_ranking_via_gen_model(mongo_docs=mongo_docs,
                                    query=query,
                                    gen_model=gen_model,
                                    n_results=re_rank_n_results)
    generation(gen_model=gen_model,
            top_docs=top_docs,
            query=query)
    unload_gen_model(gen_model)

def ingestion_retrieval_generation_without_re_ranking(flag,pdf_directory_path,text_directory_path,simple_text_var,mongo_url,
                                   mongo_database_name,mongo_collection_name,chroma_collection_name,
                                   chroma_host,chroma_port,embedding_model_path,gen_model_path,
                                   query,gen_n_ctx,gen_n_batch,embed_n_ctx,embed_n_batch,
                                   retrieve_n_results):#flag=0 =>both pdf and text,flag=1=>only pdf,flag=2=>only text,flag=3=>simple text variable
    pdf_dir_content=[]
    text_dir_content=[]
    if flag==0 or flag==1:
        pdf_dir_content=documents_loader(source=pdf_directory_path,
                                        file_type=FileType.PDF)
    if flag==0 or flag==2:
        text_dir_content=documents_loader(source=text_directory_path,
                                    file_type=FileType.TXT)
    if flag==3:
        text_dir_content=documents_loader(source=simple_text_var,
                                          file_type=FileType.SIMPLE_TEXT)
    dir_content=pdf_dir_content+text_dir_content
    docs=split_documents(dir_content=dir_content,
                        chunk_size=1000,
                        chunk_overlap=400)
    mongo_collection,chroma_collection=dbConnect(mongo_url=mongo_url,
                                                chroma_host=chroma_host,
                                                chroma_port=chroma_port,
                                                mongo_database_name=mongo_database_name,
                                                mongo_collection_name=mongo_collection_name,
                                                chroma_collection_name=chroma_collection_name)
    embedding_model=load_embedding_model(model_path=embedding_model_path,
                                        processor=Processor.GPU,
                                        n_ctx=embed_n_ctx,
                                        n_batch=embed_n_batch)
    ingest_documents(docs=docs,
                    mongo_collection=mongo_collection,
                    chroma_collection=chroma_collection,
                    embedding_model=embedding_model)
    query_vec=create_query_vector(query=query,
                                embedding_model=embedding_model)
    unload_embedding_model(embedding_model)
    mongo_docs=retrieve(mongo_collection=mongo_collection,
                        chroma_collection=chroma_collection,
                        query_vec=query_vec,
                        n_results=retrieve_n_results)
    gen_model=load_gen_model(model_path=gen_model_path,
                            processor=Processor.GPU,
                            n_ctx=gen_n_ctx,
                            n_batch=gen_n_batch)
    generation(gen_model=gen_model,
            top_docs=mongo_docs,
            query=query)
    unload_gen_model(gen_model)

def retrieval_generation(mongo_url,mongo_database_name,mongo_collection_name,chroma_collection_name,
                        chroma_host,chroma_port,embedding_model_path,gen_model_path,
                        query,gen_n_ctx,gen_n_batch,embed_n_ctx,embed_n_batch,
                        retrieve_n_results,re_rank_n_results):
    mongo_collection,chroma_collection=dbConnect(mongo_url=mongo_url,
                                                chroma_host=chroma_host,
                                                chroma_port=chroma_port,
                                                mongo_database_name=mongo_database_name,
                                                mongo_collection_name=mongo_collection_name,
                                                chroma_collection_name=chroma_collection_name)
    embedding_model=load_embedding_model(model_path=embedding_model_path,
                                        processor=Processor.GPU,
                                        n_ctx=embed_n_ctx,
                                        n_batch=embed_n_batch)
    query_vec=create_query_vector(query=query,
                                embedding_model=embedding_model)
    unload_embedding_model(embedding_model)
    mongo_docs=retrieve(mongo_collection=mongo_collection,
                        chroma_collection=chroma_collection,
                        query_vec=query_vec,
                        n_results=retrieve_n_results)
    gen_model=load_gen_model(model_path=gen_model_path,
                            processor=Processor.GPU,
                            n_ctx=gen_n_ctx,
                            n_batch=gen_n_batch)
    top_docs=re_ranking_via_gen_model(mongo_docs=mongo_docs,
                                    query=query,
                                    gen_model=gen_model,
                                    n_results=re_rank_n_results)
    generation(gen_model=gen_model,
            top_docs=top_docs,
            query=query)
    unload_gen_model(gen_model)

def retrieval_generation_without_re_ranking(mongo_url,mongo_database_name,mongo_collection_name,chroma_collection_name,
                        chroma_host,chroma_port,embedding_model_path,gen_model_path,
                        query,gen_n_ctx,gen_n_batch,embed_n_ctx,embed_n_batch,
                        retrieve_n_results):
    mongo_collection,chroma_collection=dbConnect(mongo_url=mongo_url,
                                                chroma_host=chroma_host,
                                                chroma_port=chroma_port,
                                                mongo_database_name=mongo_database_name,
                                                mongo_collection_name=mongo_collection_name,
                                                chroma_collection_name=chroma_collection_name)
    embedding_model=load_embedding_model(model_path=embedding_model_path,
                                        processor=Processor.GPU,
                                        n_ctx=embed_n_ctx,
                                        n_batch=embed_n_batch)
    query_vec=create_query_vector(query=query,
                                embedding_model=embedding_model)
    unload_embedding_model(embedding_model)
    mongo_docs=retrieve(mongo_collection=mongo_collection,
                        chroma_collection=chroma_collection,
                        query_vec=query_vec,
                        n_results=retrieve_n_results)
    gen_model=load_gen_model(model_path=gen_model_path,
                            processor=Processor.GPU,
                            n_ctx=gen_n_ctx,
                            n_batch=gen_n_batch)
    generation(gen_model=gen_model,
            top_docs=mongo_docs,
            query=query)
    unload_gen_model(gen_model)

#===========================================================================================
#================================ MAKING TOOLS AFTER THIS ==================================
#===========================================================================================
mongo_url=os.getenv("MONGO_BASE_URL")
embedding_model_path=os.getenv("QWEN_EMBEDDING_MODEL_PATH")

chroma_host=os.getenv("CHROMA_HOST")
chroma_port=os.getenv("CHROMA_PORT")
mongo_database_name=os.getenv("MONGO_DATABASE_NAME")
mongo_collection_name=os.getenv("MONGO_COLLECTION_NAME")
chroma_collection_name=os.getenv("CHROMA_COLLECTION_NAME")

embed_n_ctx=8192*3
embed_n_batch=512

def retrieval_from_context(search_query,context,retrieve_n_results,chunk_size=1000,chunk_overlap=400):
    dir_content=documents_loader(source=context,
                                          file_type=FileType.SIMPLE_TEXT)
    docs=split_documents(dir_content=dir_content,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap)
    mongo_collection,chroma_collection=dbConnect(mongo_url=mongo_url,
                                                chroma_host=chroma_host,
                                                chroma_port=chroma_port,
                                                mongo_database_name=mongo_database_name,
                                                mongo_collection_name=mongo_collection_name,
                                                chroma_collection_name=chroma_collection_name)
    embedding_model=load_embedding_model(model_path=embedding_model_path,
                                        processor=Processor.GPU,
                                        n_ctx=embed_n_ctx,
                                        n_batch=embed_n_batch)
    ingest_documents(docs=docs,
                    mongo_collection=mongo_collection,
                    chroma_collection=chroma_collection,
                    embedding_model=embedding_model)
    query_vec=create_query_vector(query=search_query,
                                embedding_model=embedding_model)
    unload_embedding_model(embedding_model)
    mongo_docs=retrieve(mongo_collection=mongo_collection,
                        chroma_collection=chroma_collection,
                        query_vec=query_vec,
                        n_results=retrieve_n_results)
    delete_mongo_collection(mongo_database_name,mongo_collection,mongo_url)
    delete_chroma_collection(chroma_host,chroma_port,chroma_collection_name)
    return mongo_docs #list of dicts
# def give_context_to_search_query

gen_n_ctx=13000
gen_n_batch=512
gen_model_path=os.getenv("DEEPSEEK_REASONING_MODEL_PATH")

def modified_generation(gen_model,top_docs,query,prompt_path,before_formated_words,after_formated_words):
    # Use 'top_5_docs' instead of 'mongo_docs'
    context_str = "\n".join([f"- {d.get('page_content', '')}" for d in top_docs])
    if prompt_path=="":
        prompt = f"""<|im_start|>system
    You are a helpful research assistant. 
Your task is to answer the user's question using ONLY the provided documents.

GUIDELINES:
1. If the documents mention specific methods (e.g., DPR, Dense Retrieval), describe them and what the text says about their performance.
2. Do NOT use outside knowledge.
3. If the documents do not contain the answer, summarize what *is* discussed in the documents instead.
    Context:
    {context_str}<|im_end|>
    <|im_start|>user
    {query}<|im_end|>
    <|im_start|>assistant
    """
    else:
        with open(prompt_path,"r") as f:
            prompt=f.read()
        len1=len(before_formated_words)
        len2=len(after_formated_words)
        if len1!=len2:
            raise ValueError("[Error] length of before formatted words array not equal to after formatted words array")
        for i in range(len1):
            prompt = prompt.replace(f"{{{before_formated_words[i]}}}", after_formated_words[i])

    print(f"\nprompt:{prompt}")
    print("\n--- AGENT THINKING ---")

    # Stream Generation
    stream = gen_model(
        prompt, 
        max_tokens=None, 
        stop=["<|im_end|>"], 
        stream=True, 
        temperature=0.6
    )

    for output in stream:
        token = output['choices'][0]['text']
        print(token, end='', flush=True)

    print("\n")
    print("================ DONE =====================")

def generation_from_context(mongo_docs,search_query):
    gen_model=load_gen_model(model_path=gen_model_path,
                            processor=Processor.GPU,
                            n_ctx=gen_n_ctx,
                            n_batch=gen_n_batch)
    context_str = "\n".join([f"- {d.get('page_content', '')}" for d in mongo_docs])
    modified_generation(gen_model=gen_model,
            top_docs=mongo_docs,
            query=search_query,
            prompt_path="../prompts/generation_with_context.txt",
            before_formated_words=["context_str","query"],
            after_formated_words=[context_str,search_query])
    unload_gen_model(gen_model)