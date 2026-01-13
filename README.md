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

16 dec 2025:
-completed react,websockets,learnt to use vector database on basic level and implementation of basic rag
-completed some of the tools:like rag,scrapping,search query generation for agent
next to complete:
-remaining tools
-explore various apis which can be given as tools to agent
-bring conversation model styled frontend to agent
-apply websockets in it for better ui experience of text appearing
-improve the prompts/architecture 
-read rag papers,agentic ai architectures for improvements
-langchain,langgraph,mcp,rl fine tuning,etc

18 dec 2025:
-now task is to how normal,vector database would look like for state management in agent
-so learn about agentic architectures or lang-graph, lang-chain,etc
-convert backend into typescript too(Frontend converted to ts done)

19 dec 2025:
-read coala paper

20 dec 2025:
to do on immediate basis:
-server.js->server.ts ,update types.ts db.js->db.ts
-update db.ts
-write agent loop
-write prompting strategies

21 dec 2025:
completed: 
-server.js->server.ts,db.js->db.ts
-updated types.ts,types.tsx,py_types.py for lots of types
-wrote basic prototype of agent loop: some 2-3 functions remaining
-implemented websockets for communication with ts server for giving approval,feedback=>though feedback loop in agentic loop is remaining

to be done further:
-2-3 functions in server.ts
-approval,feedback loop in agentic loop
-write fast api server routes which are not completed
-write prompting strategies

22 dec 2025:
remaining:
-prompts
-tools

12 jan 2026:
currently integrating website frontend websockets and other stuff, testing prompts 
next issue to resolve: working memory schema for node backend to python backend is bit different so encountering 422 error, so fix "updateState" function from server.ts

13 jan 2026:
fixed "generate-working-memory" route input output 
next to do: 1.integrate the feedback and actual prompt given by user
2. **major work**:also save all the incoming messages to and from server which has to be permanently shown to user even if it wouldnt be part of usual chat_history and working memory
3. start working on next "/reasoning"

14 jan 2026:
added feature to save all incoming message to and from server in completeHistoryModel 
next to do: -integrate historyChat and extraContent into 1 variable because both give same content
but look much different and fix some bugs too
-other stuff written in "next to do" from yesterday