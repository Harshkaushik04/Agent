from tools.model import clean_memory,i_run_model,run_model,load_model
from tools.search_query_generation import i_search_query_generation
from tools.search_engine_1 import i_search_engine_1
from tools.search_engine_2 import i_search_engine_2
from tools.html_cleaner import i_html_cleaner
from tools.make_rag_database import i_make_rag_database
from tools.retrieval_from_database import i_retrieval_from_database
from tools.question_answer import i_question_answer
from tools.generation_from_context import i_generation_from_context
from tools.summarise import i_summarise
import asyncio
from dotenv import load_dotenv
import os

load_dotenv("/home/harsh/RAG/Agent-with-ui/.env")
gen_model_path=os.getenv("DEEPSEEK_REASONING_MODEL_PATH")
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
    llm=load_model(model_path=gen_model_path,
               n_ctx=80000)
    # results = asyncio.run(test_search_engine_1())
    # print(results)
    # results = asyncio.run(test_search_engine_2())
    # print(results)
    # results=i_html_cleaner([{'url': 'https://en.wikipedia.org/wiki/North_Korean_Embassy_in_Madrid_incident', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_13134ca9.html'}, {'url': 'https://www.bbc.com/news/world-europe-47553804', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_ddd91a65.html'}, {'url': 'https://www.cnn.com/2019/03/19/politics/north-korea-embassy-madrid-intl/', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_7c9d12e7.html'}, {'url': 'https://apnews.com/article/d4d3b2276f1b478fa0955c1000003217', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_e5d05513.html'}, {'url': 'https://apnews.com/article/greenland-us-options-takeover-trump-denmark-86790903847fc8ffc27334ccb64985a9', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_3d851853.html'}, {'url': 'https://www.usatoday.com/story/graphics/2026/01/14/greenland-us-map-why-does-trump-want-it/88142859007/', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_a4f6cd2e.html'}, {'url': 'https://www.cnbc.com/2026/01/09/nato-trump-greenland-war-invade-defense.html', 'file_store_path': '/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html/raw_a26f6190.html'}])
    # print(results)
    # result=i_make_rag_database(["/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/cleaned_text/clean_raw_3d851853.html.txt",
    #                             "/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/cleaned_text/clean_raw_7c9d12e7.html.txt",
    #                             "/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/cleaned_text/clean_raw_13134ca9.html.txt",
    #                             "/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/cleaned_text/clean_raw_a4f6cd2e.html.txt",
    #                             "/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/cleaned_text/clean_raw_a26f6190.html.txt",
    #                             "/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/cleaned_text/clean_raw_ddd91a65.html.txt",
    #                             "/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/cleaned_text/clean_raw_e5d05513.html.txt"])
    # print(result)
    # results=i_retrieval_from_database(database_details={
    #     "mongo_database":"RAG",
    #     "mongo_collection":"rag_collection_8498472f",
    #     "chroma_collection":"rag_collection_8498472f"
    # },list_search_query_top_k=[{
    #     "search_query":"does usa have an agreement with greenland?",
    #     "top_k":3
    # },
    # {
    #     "search_query":"how many victims were attcaked in north korean embassy attack in spain?",
    #     "top_k":2
    # }])
    # print(results)
#     content=i_generation_from_context(llm=llm,
#                               whether_path_or_data="data",
#                               context="""6-7 meme

#     Article
#     Talk

#     Read
#     View source
#     View history

# Tools

# Appearance
# Text

#     Small
#     Standard
#     Large

# Width

#     Standard
#     Wide

# Color (beta)

#     Automatic
#     Light
#     Dark

# Page semi-protected
# From Wikipedia, the free encyclopedia
# A jack-o'-lantern with 6-7 carved into it

# 6-7 (pronounced "six seven"; also written as 67 or 6 7) is an Internet meme and slang term that emerged in 2025 on TikTok and Instagram Reels,[1] and later spread to YouTube Shorts. It has no fixed meaning.[2]

# The phrase originated from the song "Doot Doot (6 7)" by Skrilla, which became popular in video edits featuring professional basketball players, especially LaMelo Ball, who is listed at 6 ft 7 in (2.01 meters) tall.[3][4] The meme was further popularized through Overtime Elite player Taylen "TK" Kinney's repeated use of the phrase.[5] In March 2025, a boy named Maverick Trevillian became known as the "67 Kid" after a viral video showed him yelling the term at a basketball game while performing an excited hand gesture.[6]

# The meme, described as "annoying" and "like a plague",[7] has been linked by multiple news outlets to the wider "brain rot" phenomenon—digital media deemed to be of poor quality.[8] Some commentators also see it as evidence of Generation Alpha's growing presence in Internet culture.[9]
# Origin
# Main article: Doot Doot (6 7)
# A photo of a sidewalk with chalk writing that reads "What's 6+7?"
# Sidewalk chalk art referencing 6-7 on the campus of Washington University

# The slang originated from the drill rap song "Doot Doot (6 7)", in which American rapper Skrilla raps, "... I know he dyin' (oh my, oh my God) 6-7, I just bipped right on the highway (Bip, bip)" as the beat drops.[10][11]

# The meaning of the number in the song remains ambiguous: some have connected it to 67th Street in Skrilla's hometown of Philadelphia,[12] or to 67th Street in Chicago.[13][10] Linguist and African-American English expert Taylor Jones has speculated that it may refer to "10-67", the ten-code used by Philadelphia police to notify officers of a death.[14]: 9:36 [citation needed] This aligns with the previous lines' descriptions of gun violence and his interpretation that the line depicts the narrator playing innocent during a traffic stop.[14]: 7:20  Skrilla himself stated, "I never put an actual meaning on it, and I still would not want to."[12]

# The song was unofficially released in December 2024[15] and officially released on February 7, 2025.[16] It was soon used in video edits of professional basketball players, particularly LaMelo Ball, who is 6 ft 7 in (2.01 m) tall.[15] A few weeks after the song's unofficial release,[17] Taylen Kinney, a high school basketball prospect at Overtime Elite, became strongly associated with the phrase after a clip of him ranking a Starbucks drink by saying "six, seven" went viral on social media.[5][18] His repeated use of the phrase during Overtime Elite content led to his nickname "Mr. 6-7", and he later launched a "6-7"-branded canned water line.[5][18]
# Spread
# Duration: 3 seconds.0:03Subtitles available.CC
# A person doing the gesture associated with the meme "6-7"

# The meme has been referenced in NBA highlights, WNBA news conferences, NFL touchdown celebrations, and by celebrities, including former NBA player Shaquille O'Neal, who participated in a video referring to it despite admitting he did not understand its meaning. Additionally, the term has been frequently used throughout college sports.[19][5]

# As the meme expanded beyond sports, social media users began to employ the meme in unrelated contexts, such as joking about getting a score of 67% on an exam.[20] 6-7's identity as a slang term has allowed it to spread in offline contexts, especially in schools,[9] with some banning its use due to disruption in classrooms.[21] In November 2025, British Prime Minister Keir Starmer apologized to a headteacher after joining schoolchildren in the gesture when a schoolgirl sitting next to him noted the book they were reading was turned to pages 6 and 7; the gesture had been banned at the school.[22][23][24][25][15] Lawmaker Bill Buckbee, who represents the 67th District in the Connecticut House of Representatives, jokingly used the phrase during a special legislative session.[26] Representative Blake Moore of Utah's 1st congressional district also made reference to the trend while presiding over the United States House of Representatives on November 18, 2025.[27] In December 2025, U.S. vice president JD Vance jokingly proposed to ban the use of the phrase after his 5-year-old child screamed 6-7 in the middle of a church service. Vance stated: "And now I think we need to make this narrow exception to the First Amendment and ban these numbers forever."[28]

# The moniker "Mason" has been used to refer to a stereotypical white high school boy who overuses the slang.[29]
# 67 Kid
# Maverick Trevillian, better known as the "67 Kid", at a fan meetup in Venice Beach, California, 2025

# On March 31, 2025, YouTuber Cam Wilder posted a video titled "My Overpowered AAU Team has Finally Returned!" (stylized in all caps) in which a young boy, Maverick Trevillian[6]—later nicknamed "67 Kid"—is seen yelling "six seven" while performing a hand gesture in which he moves his hands up and down with upward-facing palms.[29][30][31]

# In August 2025, social media users began creating photo edits distorting Trevillian in a bizarre or grotesque fashion, likened to analog horror. This meme, called "SCP-067 Kid", satirizes the SCP Foundation, a collaborative fiction project about paranormal anomalies. "SCP-067 Kid" is not related to the canon "SCP-067", which is about a supernatural fountain pen.[29][32][33]
# Variants

# 41 (pronounced "forty-one") is a meme of similar origin, deriving from the song "41 Song (Saks Freestyle)" in which rapper Blizzi Boi raps the number throughout.[34][35] Another variant is 6-1 (pronounced "seeks-wahn"), created by TikTok creator Spartan Swot.[36]
# Use by media and brands
# Chicken nuggets from McDonald's UAE with the special "6(7)" sticker

# On October 16, 2025, the 1st episode of season 28 of the adult animated show South Park aired[37] with a prominent plot point in which the children are brainwashed by the 6-7 meme. This season of South Park, along with season 27, also targeted other online trends such as Labubu, TikTok, and prediction markets.[38]

# In October, the mobile game Clash Royale added an emote referencing the meme after its Instagram account reached 6.7 million followers.[39] On November 5, first-person shooter video game Overwatch 2 announced that it would be adding a "67" emote to the game.[40] On November 29, 2025, Fortnite Battle Royale teased their new Chapter 7 update with a reference to the 6-7 meme.[41] Following the update's release, the emote made its debut.[42]

# From November 6 to 7, Pizza Hut sold chicken wings for 67 cents each.[43][44] During the same period, McDonald's in the United Arab Emirates gave away free chicken nuggets between 6 and 7 pm. Each 6-piece chicken pack featured a special "6(7)" sticker and contained seven nuggets instead of the usual six.[45] Domino's offered members a one-topping pizza for $6.70 when they used the promo code "67".[46] Later, in December 2025, Google introduced an Easter egg in which typing "6-7", "67", or "6 7" causes a user's screen to shake up and down, mimicking the gesture associated with the meme.[47] Restaurant chain In-N-Out removed the number "67" from its ordering system after teenagers began to scream whenever the number was called out.[48]
# Reception

# Multiple news outlets, such as Business Insider, have attributed the meme to the wider phenomenon of brain rot—the spread of digital media considered to be of poor quality.[8] Many viewed the meme as a sign of Generation Alpha's increasing involvement in Internet culture.[9]

# In October 2025, Dictionary.com named "67" as its 2025 Word of the Year, describing the interjection as "a burst of energy that spreads and connects people long before anyone agrees on what it actually means".[49] The Merriam-Webster dictionary defines it as "a nonsensical expression connected to a song and a basketball player".[50] The Swedish Institute for Language and Folklore (Institutet för språk och folkminnen) included "six seven" in its 2025 new word list, also defining it as "a nonsensical expression".[51][52]

# During the Christmas season, several variants of Christmas songs incorporating the 6-7 meme and other brain rot terms were popular on platforms such as TikTok. One example was "67 Merry Rizzmas."[53]

# Alphonse Pierre of Pitchfork lamented that, in exchange for virality, Skrilla had been reduced to a one-dimensional mascot, and "not a human artist with music packed with complicated views and morals worth considering".[17] """,
# query="how did 6-7 meme originate?")
#     print(content)
    # content=i_question_answer(llm=llm,
    #                           query="donald trump vs joe biden")
    content=i_summarise(llm=llm,
                        whether_path_or_data="path",
                        text="/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/cleaned_text/clean_raw_3d851853.html.txt")
    print(content)
    clean_memory(llm)