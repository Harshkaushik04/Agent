from dotenv import load_dotenv
import os
from rag_functions import clean_memory,documents_loader,split_documents,dbConnect,load_embedding_model,unload_embedding_model,ingest_documents,create_query_vector,retrieve,load_gen_model,unload_gen_model,re_ranking_via_gen_model,generation,delete_mongo_collection,delete_chroma_collection,ingestion_retrieval_generation,retrieval_generation,ingestion_retrieval_generation_without_re_ranking,retrieval_generation_without_re_ranking,Processor,FileType
load_dotenv()

mongo_url=os.getenv("MONGO_URL") 
chroma_host=os.getenv("CHROMA_HOST")
chroma_port=os.getenv("CHROMA_PORT")
pdf_directory_path=os.getenv("PDF_DIRECTORY_PATH")
text_directory_path=os.getenv("TEXT_DIRECTORY_PATH")
embedding_model_path=os.getenv("EMBEDDING_MODEL_PATH")
gen_model_path=os.getenv("GEN_MODEL_PATH")
mongo_database_name=os.getenv("MONGO_DATABASE_NAME")
mongo_collection_name=os.getenv("MONGO_COLLECTION_NAME")
chroma_collection_name=os.getenv("CHROMA_COLLECTION_NAME")

which_to_run=int(input("Which to run:"))
#if 0=>everything without re ranking, 1=>generation without re ranking 2=> delete
if which_to_run==0 or which_to_run==1:
    query=input("QUERY:")
if which_to_run==0:
    ingestion_retrieval_generation_without_re_ranking(flag=1,
                               pdf_directory_path=pdf_directory_path,
                               text_directory_path=text_directory_path,
                               mongo_url=mongo_url,
                               mongo_database_name=mongo_database_name,
                               mongo_collection_name=mongo_collection_name,
                               chroma_host=chroma_host,
                               chroma_port=chroma_port,
                               chroma_collection_name=chroma_collection_name,
                               embedding_model_path=embedding_model_path,
                               gen_model_path=gen_model_path,
                               query=query,
                               gen_n_ctx=12000,
                               gen_n_batch=512,
                               embed_n_ctx=8192*3,
                               embed_n_batch=512,
                               retrieve_n_results=5)
if which_to_run==2:
    delete_chroma_collection(chroma_host=chroma_host,
                         chroma_port=chroma_port,
                         chroma_collection=chroma_collection_name)
    delete_mongo_collection(mongo_database=mongo_database_name,
                        mongo_collection=mongo_collection_name,
                        mongo_url=mongo_url)
if which_to_run==1:
    retrieval_generation_without_re_ranking(mongo_url=mongo_url,
                    mongo_database_name=mongo_database_name,
                    mongo_collection_name=mongo_collection_name,
                    chroma_host=chroma_host,
                    chroma_port=chroma_port,
                    embedding_model_path=embedding_model_path,
                    chroma_collection_name=chroma_collection_name,
                    gen_model_path=gen_model_path,
                    query=query,
                    gen_n_ctx=12000,
                    gen_n_batch=512,
                    embed_n_ctx=8192*3,
                    embed_n_batch=512,
                    retrieve_n_results=5)