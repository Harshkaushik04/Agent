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

class FunctionToExecuete(TypedDict):
    function_name:str
    inputs:Dict[str,str]

class ThingsToNode(TypedDict):
    serial_number:int
    description:str
    content:str

# 2. Main Working Memory Schema

class WorkingMemorySchema(TypedDict):
    chat_history: List[ChatMessage]
    previous_actions_and_logs: List[ActionLog]
    final_goal: str
    current_goal: str
    rough_plan_to_reach_goal: List[PlanStep]
    summaries: List[Summary]
    env_state: EnvState
    episodic_memory_descriptions: List[EpisodicMemory]
    function_to_execuete:FunctionToExecuete
    things_to_note:List[ThingsToNode]
    final_goal_completed:bool

class Message():
    role: str
    content: str
    before_think: Optional[str] = ""
    after_think: Optional[str] = ""

class GenerateRequest(TypedDict):
    working_memory:WorkingMemorySchema

__all__=[WorkingMemorySchema,ChatMessage,ActionLog,PlanStep,Summary,Message,GenerateRequest]