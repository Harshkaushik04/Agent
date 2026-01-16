from rag_functions import retrieval_from_context,generation_from_context
from complete_search_engine import complete_search
from search_query_generation import i_search_query_generation
import asyncio

async def run():
    search_query="list of asmongold controversies over the years?"
    # top_k=int(input("top k:"))
    # retrieve_n_results=int(input("retrieve n results:"))
    # chunk_size=int(input("chunk size:"))
    # chunk_overlap=int(input("chunk overlap:"))
    search_queries=i_search_query_generation(search_query,"../prompts/second_phase_search_query_generation.txt",
                                           ["user_query","previous_search_queries","context"],[search_query,"""{
  "questions": [
    "ASMONGOLD trends 2025",
    "ASMONGOLD controversies overview",
    "ASMONGOLD issues recent",
    "ASMONGOLD disputes 2025",
    "ASMONGOLD disputes explained"
  ]
}
"""],"""""")
    combined_context=""
    for query in search_queries:
        context=await complete_search(search_query=query,
                        top_k=top_k)
        combined_context+=context
        combined_context+="\n"
    top_docs=retrieval_from_context(search_query=search_query,
                                    context=combined_context,
                                    retrieve_n_results=retrieve_n_results,
                                    chunk_size=chunk_size,
                                    chunk_overlap=chunk_overlap)
    final_generated=generation_from_context(mongo_docs=top_docs,
                                        search_query=search_query)
    
asyncio.run(run())