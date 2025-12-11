from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader,DirectoryLoader,PyPDFLoader,PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymongo import MongoClient
import chromadb
from llama_cpp import Llama
from bson.objectid import ObjectId
import torch,gc

MONGO_URL="mongodb://localhost:27017"
CHROMA_HOST="localhost"
CHROMA_PORT=8000

PDF_DIRECTORY_PATH="data/papers"
TEXT_DIRECTORY_PATH="data/text_files"
EMBEDDING_MODEL_PATH="../../models/gte-Qwen2-1.5B-instruct-f16.gguf"
GEN_MODEL_PATH="../../models/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"

QUERY="What are the different methods of data ingestion in rag and explain them in detail"

def clean_memory(model):
    if model:
        del model
    gc.collect()
    torch.cuda.empty_cache()

print("================PHASE 1=====================")
pdf_dir_loader=DirectoryLoader(path=PDF_DIRECTORY_PATH,
                               glob="**/*.pdf",
                               loader_cls=PyMuPDFLoader)
text_dir_loader=DirectoryLoader(path=TEXT_DIRECTORY_PATH,
                                glob="**/*.txt",
                                loader_cls=TextLoader)
pdf_dir_content=pdf_dir_loader.load()
text_dir_content=text_dir_loader.load()


text_splitter=RecursiveCharacterTextSplitter(separators=["\n","\n\n",""," "],
                                             chunk_size=1000,
                                             chunk_overlap=200)
pdf_docs=text_splitter.split_documents(pdf_dir_content)
text_docs=text_splitter.split_documents(text_dir_content)


print("================PHASE 2=====================")
mongo_collection=MongoClient(MONGO_URL)["RAG"]["rag_docs"]
chroma_client=chromadb.HttpClient(host=CHROMA_HOST,port=CHROMA_PORT)
chroma_collection=chroma_client.get_or_create_collection("rag_index")

print("================PHASE 3=====================")
embedding_model=Llama(model_path=EMBEDDING_MODEL_PATH,
                      n_gpu_layers=-1,
                      n_ctx=8192*3,
                      n_batch=512,
                      embedding=True)

print("================PHASE 4=====================")
for doc in pdf_docs:
    pdf_doc_id=str(mongo_collection.insert_one({"page_content":doc.page_content,"metadata":doc.metadata}).inserted_id)
    vec_data=embedding_model.create_embedding(doc.page_content)
    vec=vec_data["data"][0]["embedding"]
    chroma_collection.add(ids=[pdf_doc_id],embeddings=[vec],metadatas=[doc.metadata])

for text in text_docs:
    text_docs_id=str(mongo_collection.insert_one({"page_content":text.page_content,"metadata":text.metadata}).inserted_id)
    vec_data=embedding_model.create_embedding(text.page_content)
    vec=vec_data["data"][0]["embedding"]
    chroma_collection.add(ids=[text_docs_id],embeddings=[vec],metadatas=[text.metadata])

query_vec_data=embedding_model.create_embedding(QUERY)
query_vec=query_vec_data["data"][0]["embedding"]
clean_memory(embedding_model)
print("================PHASE 5=====================")
results=chroma_collection.query(query_embeddings=[query_vec],n_results=5)
retrieved_ids=[ObjectId(i) for i in results['ids'][0]]
mongo_docs=list(mongo_collection.find({"_id":{"$in":retrieved_ids}}))

print("================PHASE 6=====================")
context_str = "\n".join([f"- {d['page_content']}" for d in mongo_docs])
prompt = f"""<|im_start|>system
You are a precise research assistant.
Answer the user's question using ONLY the facts from the Context provided below.
If the Context does not contain the answer, say "The provided documents do not contain this information."
DO NOT use your own outside knowledge. DO NOT make up lists.
Context:
{context_str}<|im_end|>
<|im_start|>user
{QUERY}<|im_end|>
<|im_start|>assistant
"""
print("prompt:",prompt)
gen_model=Llama(model_path=GEN_MODEL_PATH,
                n_gpu_layers=-1,
                n_ctx=8192,
                n_batch=512)
for chunk in gen_model(prompt=prompt,stream=True,stop=["<|im_end|>"]):
    print(chunk['choices'][0]['text'],end='',flush=True)
print('\n')
clean_memory(gen_model)