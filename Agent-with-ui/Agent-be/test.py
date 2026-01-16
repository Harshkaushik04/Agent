from tools.model import clean_memory,i_run_model,run_model,load_model
from tools.search_query_generation import i_search_query_generation
from tools.search_engine_1 import i_search_engine_1
from tools.search_engine_2 import i_search_engine_2
from tools.html_cleaner import i_html_cleaner
import asyncio

def test_search_query_generation():
    llm = load_model(model_path="../../models/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
                      n_ctx=80000)
    search_queries_list=i_search_query_generation(llm,["which has more subscribers,neon man vs neuz boy",
                                   "is actualized.org best path for gaining freedom",
                                   "research about the attack on north korean embassy in spain"])
    clean_memory(llm=llm)
    print(search_queries_list)

async def test_search_engine_1():
    results=await i_search_engine_1([{
        "search_query":"north korea embassy attack in spain",
        "top_k":4
    },{
        "search_query":"will usa invade greenland",
        "top_k":3
    }])
    return results

async def test_search_engine_2():
    results=await i_search_engine_2(['https://en.wikipedia.org/wiki/North_Korean_Embassy_in_Madrid_incident', 'https://www.bbc.com/news/world-europe-47553804', 'https://www.cnn.com/2019/03/19/politics/north-korea-embassy-madrid-intl/', 'https://apnews.com/article/d4d3b2276f1b478fa0955c1000003217','https://apnews.com/article/greenland-us-options-takeover-trump-denmark-86790903847fc8ffc27334ccb64985a9', 'https://www.usatoday.com/story/graphics/2026/01/14/greenland-us-map-why-does-trump-want-it/88142859007/', 'https://www.cnbc.com/2026/01/09/nato-trump-greenland-war-invade-defense.html'])
    return results
if __name__ == "__main__":
    # test_search_query_generation()
    # results = asyncio.run(test_search_engine_1())
    # print(results)
    # results = asyncio.run(test_search_engine_2())
    # print(results)
    i_html_cleaner([{'url': 'https://en.wikipedia.org/wiki/North_Korean_Embassy_in_Madrid_incident', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_13134ca9.html'}, {'url': 'https://www.bbc.com/news/world-europe-47553804', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_ddd91a65.html'}, {'url': 'https://www.cnn.com/2019/03/19/politics/north-korea-embassy-madrid-intl/', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_7c9d12e7.html'}, {'url': 'https://apnews.com/article/d4d3b2276f1b478fa0955c1000003217', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_e5d05513.html'}, {'url': 'https://apnews.com/article/greenland-us-options-takeover-trump-denmark-86790903847fc8ffc27334ccb64985a9', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_3d851853.html'}, {'url': 'https://www.usatoday.com/story/graphics/2026/01/14/greenland-us-map-why-does-trump-want-it/88142859007/', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_a4f6cd2e.html'}, {'url': 'https://www.cnbc.com/2026/01/09/nato-trump-greenland-war-invade-defense.html', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_a26f6190.html'}])