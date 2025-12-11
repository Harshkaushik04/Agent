6 dec 2025:
inside fronend_client.js(frontend):

almost done with axios.post("http://localhost:3000/make-plan") 
have to work on username login and sessionNUmber system
also work on axios.post("http://localhost:3000/use-tools"):majorly in backend 

inside agent_brain.js:
layout different routes going to different tools and connect different routes to tools_server.py which uses flask 

-see how the working of links_list,paths_list,texts_list,prompt would work

7 dec 2025:
making conversation-model in which we can do inference with models, it does login auth,can use multiple models, stores history of different chats
login,signup,landingpage both frontend and backend v1 is done
for chat page, frontend v1 is done, backend v1 has to be done, also implement rag for extracting things from history when context is long
after that revert back to Agent project where make tools 

conversation-model:
-can add jwt token in every user sent thing which server is relieing on like model,char number,etc:will do later
9 dec 2025:
things to improve:
include vector database for rag in conversation model app, learn more about react to make code more readable
learn websockets so that the text appears as soon as model starts generating
add dropdown menu for model we can use
add better formating to text given out by llm specially to code or points

so plan:
-complete react
-complete websockets
-apply websockets in conversation model
-learn how to use vector database in mongo db
-implement rag in conversation model
-go back to tools in Agent

more things to learn:
langchain,lang graph
MCP
computer upse and multimodal agents
RL fine tuning
memory framework