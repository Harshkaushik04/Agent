from typing import TypedDict, List, Dict,Optional

# 1. Define Sub-Types first for cleaner structure

class ChatMessage(TypedDict):
    serial_number:int
    role: str
    content: str

class ActionLog(TypedDict):
    serial_number: int
    description: str
    function: str
    inputs: Dict[str, str]   # Matches { [key:string]: string }
    outputs: Dict[str, str]
    log: str
    filter_words: List[str]

class PlanStep(TypedDict):
    serial_number: int
    description: str
    function: str
    inputs: Dict[str, str]
    brief_expected_outputs: Dict[str, str]
    status: str

class Summary(TypedDict):
    serial_number:int
    description: str
    content: str
    filter_words: List[str]

class EnvState(TypedDict):
    serial_number:int
    description: str
    content: str

class EpisodicMemory(TypedDict):
    serial_number:int
    episodic_memory_description:str

# 2. Main Working Memory Schema

class WorkingMemorySchema(TypedDict):
    chat_history: List[ChatMessage]
    
    previous_actions_and_logs: List[ActionLog]
    
    final_goal: str
    current_goal: str
    
    # In your TS, this was a single object, not an array
    rough_plan_to_reach_goal: PlanStep
    
    # In your TS, this was a single object
    summaries: Summary
    
    env_state: EnvState
    
    episodic_memory_descriptions: List[EpisodicMemory]

class Message():
    role: str
    content: str
    before_think: Optional[str] = ""
    after_think: Optional[str] = ""

class GenerateRequest(TypedDict):
    working_memory:WorkingMemorySchema

__all__=[WorkingMemorySchema,ChatMessage,ActionLog,PlanStep,Summary,Message,GenerateRequest]