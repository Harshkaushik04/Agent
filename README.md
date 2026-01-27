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

15 jan 2026:
removed the buggy extraContent variable and integrated it into historyChat for consistency
next to do:
1. write prompts for next routes like reasoning,etc and also integrate feedback,etc
2. learn next.js 

completed:written prompts for reasoning, added safe gaurd to kill py server
update to "/execuete" route: only output log and not stateUpdationObject(only run tool and not llm call)
next to do: 1.make all the tools to be used in "/execuete"
2. after making all tools, make prompt for "make-log" and then fully test the system
3. make better ui for formatting chats

17 jan 2026:
added tools for agents: search_query_generation,search_engine_1,search_engine_2,write_file,read_file,merged_files,html_cleaner,file_checker

new thing proposed: add a field of "satisfied" when returning from "/execuete" or "/interpret-output" 
routes, if satisfied is no=> repeat the route, effectively creating method to rerun these routes till 
they are satisfied

also changed name of "/make-log" to "/interpret-output"

18 jan 2026:
completed all the tools except "video/audio to text" one
started learning next.js(intro)
next to do: 
1. complete "video/audio to text" tool
2. complete "/execuete","/interpret-output" and "/update-working-memory" route and also apply "satisfied"
field in execuete and interpret-output=> then test the whole loop
3. learn next.js

21 jan 2026:
to do next:
1. write prompts for "/execuete","interpret-output" and "/update-working-memory" routes

things to note:
1-> updated structure of agent to 
generate_working_memory -> reasoning -> execuete(running+ then llm)[this step can run multiple times without intervention of reasoning based on instruction of llm("satisifaction of llm")] -> go back to reasoning

overview of tasks done by each step:
1. generate_working_memory: edit state such that state is ready to do new task given by user and erase
irrelevent stuff from previous user prompts(still keep some meory because it might be needed for context of what user is asking(maybe transfer majority of things in some kind of seperate memory))

2. reasoning: if this is the first reasoning step => then make rough_plan_to_reach_goal and basically make a plan by updating all the relevent fields
if its step after the execuete step => then it has these tasks:
(a) reflect on whether current plan of action is correct or not in order to acheive the final goal => update relevent fields accordingly
(b) garbage removal: if some context is not needed anymore in the working memory then remove it

3. execuete: this step can run multiple times consecutively if reasoning isnt needed,
first function is run from current_function_to_execuete field and then llm summarises log to 
edit previous_actions_and_logs, decides whether its "satisfied" and want to give control to reasoning step or not, also can update the plan according to whether function can successfully or not, etc

2-> "satisfied" field doesnt come seperately in the response by py_server but its part of stateUpdationObject and is hence processed by updateState function in server.ts 

completed: mostly done everything for v1 except these:
1. examples for reasoning and execuete
2. make schema for episodic memories and make updateEpisodicMemory function for TOOLS
3. complete some tools like video_to_text, audio_to_text,etc

27 jan 2026:
-added openrouter api routes in py_server
-added checking mechanism for stateUpdationObject sent by py_server in server.ts

-added ```json ``` formatting function
-did request checking through postman on "/execute" route and did some changes like added to_str function which converts dict/list/other types to string(stringify them)

next to do:
1. add example_execute
2. add print statements for each tool so that llm can find what really happened