from typing import TypedDict, List, Dict,Optional
from pydantic import BaseModel
# 1. Define Sub-Types first for cleaner structure

class ChatMessage(BaseModel):
    serial_number:int
    role: str
    content: str

class ActionLog(BaseModel):
    serial_number: int
    description: str
    function_name: str
    inputs: Dict[str, str]   # Matches { [key:string]: string }
    outputs: Dict[str, str]
    log: str
    filter_words: List[str]

class PlanStep(BaseModel):
    serial_number: int
    description: str
    function_name: str
    inputs: Dict[str, str]
    brief_expected_outputs: List[str]
    status: str

class Variable(BaseModel):
    serial_number:int
    variable_type:str
    description: str
    content: str
    filter_words: List[str]

class EnvState(BaseModel):
    serial_number:int
    description: str
    content: str

class EpisodicMemory(BaseModel):
    serial_number:int
    description:str

class CurrentFunctionToExecuete(BaseModel):
    function_name:str
    inputs:Dict[str,str]

class ThingsToNode(BaseModel):
    serial_number:int
    description:str
    content:str

# 2. Main Working Memory Schema

class WorkingMemorySchema(BaseModel):
    chat_history: List[ChatMessage]
    previous_actions_and_logs: List[ActionLog]
    final_goal: str
    current_goal: str
    rough_plan_to_reach_goal: List[PlanStep]
    variables:List[Variable]
    env_state: List[EnvState]
    episodic_memory_descriptions: List[EpisodicMemory]
    current_function_to_execuete:CurrentFunctionToExecuete
    things_to_note:List[ThingsToNode]
    final_goal_completed:str

class Message():
    role: str
    content: str
    before_think: Optional[str] = ""
    after_think: Optional[str] = ""

class GenerateWorkingMemoryRequest(BaseModel):
    state:WorkingMemorySchema
    feedback:str
    model:str
    chat_number:int

ReasoningRequest=GenerateWorkingMemoryRequest
ExecueteRequest=GenerateWorkingMemoryRequest

class MakeLogRequest(BaseModel):
    state:WorkingMemorySchema
    log:str
    feedback:str
    model:str
    chat_number:int

UpdateWorkingMemoryRequest=GenerateWorkingMemoryRequest

__all__ = [
    "WorkingMemorySchema", 
    "ChatMessage", 
    "ActionLog", 
    "PlanStep", 
    "Variable", 
    "Message", 
    "GenerateWorkingMemoryRequest",
    "ReasoningRequest", 
    "ExecueteRequest", 
    "MakeLogRequest", 
    "UpdateWorkingMemoryRequest"
]