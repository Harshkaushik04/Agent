import type{ NavigateFunction } from "react-router-dom"
import type { ReactNode } from "react"
import type { Request } from "express"
export type numString=number|string

//Database-data types
export type messageType={
        role:String,
        content:String,
        before_think:String,
        after_think:String,
        timestamp:Date
}
export type ApprovalMessageType={
  content:string,
  isDone:boolean,
  approved:boolean
}

//frontend component types
export interface userType{
    username:String,
    model:String,
    title:String,
    messages:messageType[]
}

export interface mainBarType{
  width1:numString,
  height1:numString,
  width2:numString,
  height2:numString,
  content:messageType[]
}

export interface sideBarType{
  width:numString,
  height:numString,
  titles:string[]
}

export interface boxType{
  title:string,
  color:string
}
export interface chatMessagesType{
  messages:messageType[],
  extraContent:ApprovalMessageType[]
}

export interface searchBarType{
  placeholder:string,
  width:numString,
  height:numString
}

//simple
export interface props{
    children:ReactNode
}

//Context types
export interface chatContextType{
    historyTitles: string[],
    setHistoryTitles: React.Dispatch<React.SetStateAction<string[]>>, 
    historyChat: messageType[],
    setHistoryChat: React.Dispatch<React.SetStateAction<messageType[]>>,
    extraContent:ApprovalMessageType[],
    setExtraContent:React.Dispatch<React.SetStateAction<ApprovalMessageType[]>>,
    Navigate: NavigateFunction
}

export interface loginContextType{
    username:string,
    setUsername:React.Dispatch<React.SetStateAction<string>>,
    password:string,
    setPassword:React.Dispatch<React.SetStateAction<string>>,
    Navigate:NavigateFunction
}

export interface signUpContextType{
    username:string,
    setUsername:React.Dispatch<React.SetStateAction<string>>,
    password:string,
    setPassword:React.Dispatch<React.SetStateAction<string>>,
    Navigate:NavigateFunction
}

//Hooks Types
export interface textAreaRefHookType{
    textareaRef:React.RefObject<HTMLTextAreaElement|null>,
    getTextAreaRefCurrent:()=>HTMLTextAreaElement
} 

export interface divRefHookType{
    divRef:React.RefObject<HTMLDivElement|null>,
    getDivRefCurrent:()=>HTMLDivElement
}


// Server response types
export type invalidResponseType={
    valid:false
}

export type i_loadHistoryTitlesType={
  valid:true,
  titles:string[]
}

export type i_loadNewChatType={
  valid:true,
  chat_number:number
}
export type i_deleteChatType=i_loadNewChatType

export type i_clickHistoryType={
    valid:true,
    value_json:messageType[]
}
export type i_updateChatType=i_clickHistoryType

export type i_sendMessageType={
    valid:true
}

export type i_loginType={
    valid:boolean,
    username:string,
    token:string
}

export type i_signUpType={
    whetherDuplicate:boolean
}

export type loadHistoryTitlesType=i_loadHistoryTitlesType|invalidResponseType
export type loadNewChatType=i_loadNewChatType|invalidResponseType
export type deleteChatType=loadNewChatType
export type clickHistoryType=i_clickHistoryType|invalidResponseType
export type updateChatType=clickHistoryType
export type sendMessageType=i_sendMessageType|invalidResponseType
export type loginType=i_loginType
export type signUpType=i_signUpType


export type wsToFrontend_approval={ 
    eventType:"approval",
    state:workingMemorySchemaType,
    stateUpdationObject?:stateUpdationType[],
    message?:string
}
export type wsToFrontend_showOutput={
    eventType:"showOutput",
    state?:workingMemorySchemaType,
    stateUpdationObject?:stateUpdationType[],
    message?:string
}

export type wsToFrontend=wsToFrontend_approval|wsToFrontend_showOutput
export type wsToBackend_approval={
    eventType:"approval",
    approval:string,
    feedback?:string,
    token:string
}
export type wsToBackend_connect={
  eventType:"connect",
  token:string
}
export type wsToBackend=wsToBackend_approval|wsToBackend_connect

export type workingMemorySchemaType={
    chat_history:chatHistoryType[],
    previous_actions_and_logs:addPreviousActionsAndLogsType[],
    final_goal:string,
    current_goal:string,
    rough_plan_to_reach_goal:roughPlanToReachGoalType[],
    summaries:summariesType[],
    env_state:envStateType[],
    episodic_memory_descriptions:episodicMemoryDescriptionsType[],
    current_function_to_execuete:currentFunctionToExecueteType,
    things_to_note:thingsToNoteType[],
    final_goal_completed:boolean
}


export type chatHistoryType={
    serial_number:number,
    role:string,
    content:string
}

export type addPreviousActionsAndLogsType={
    serial_number:number,
    description:string,
    function_name:string,
    inputs:{
        [key:string]:string
    },
    outputs:{
        [key:string]:string
    },
    log:string,
    filter_words:string[]
}

export type roughPlanToReachGoalType={
    serial_number:number,
    description:string,
    function_name:string,
    inputs:{
        [key:string]:string
    },
    brief_expected_outputs:string[],
    status:string
}

export type summariesType={
    serial_number:number,
    description:string,
    content:string,
    filter_words:string[]
}

export type envStateType={
    serial_number:number,
    description:string,
    content:string
}

export type episodicMemoryDescriptionsType={
    serial_number:number,
    description:string
}

export type currentFunctionToExecueteType={
    funcation_name:string,
    inputs:{
        [key:string]:string
    }
}

export type thingsToNoteType={
    serial_number:number,
    description:string,
    content:string
}

export type anyUpdateType=chatHistoryType|addPreviousActionsAndLogsType|roughPlanToReachGoalType|summariesType|
envStateType|episodicMemoryDescriptionsType|currentFunctionToExecueteType|thingsToNoteType|string

export type deleteAnyType={
    updateType:"delete",
    field:anyFieldType,
    serial_number:number
}

export type addAnyType={
    updateType:"add"
}& anyPair

export type updateAnyType={
    updateType:"update",
    serial_number:number,
}& anyPair

export type stateUpdationType=deleteAnyType|addAnyType|updateAnyType


export const listFieldValues = [
  "chat_history",
  "previous_actions_and_logs",
  "rough_plan_to_reach_goal",
  "summaries",
  "env_state",
  "episodic_memory_descriptions",
  "current_function_to_execuete",
  "things_to_note",
] as const;
export type listFieldType = typeof listFieldValues[number];


export const stringFieldValues =[
    "final_goal",
    "current_goal",
    "final_goal_completed"
] as const
export type stringFieldType= typeof stringFieldValues[number]
export type anyFieldType=listFieldType|stringFieldType

export type chatHistoryPair={
    field:"chat_history",
    updated:chatHistoryType
}

export type PreviousActionsAndLogsPair={
    field:"previous_actions_and_logs",
    updated:addPreviousActionsAndLogsType
}

export type stringPair={
    field:"current_goal"|"final_goal",
    updated:string
}

export type roughPlanToReachGoalPair={
    field:"rough_plan_to_reach_goal",
    updated:roughPlanToReachGoalType
}

export type summariesPair={
    field:"summaries",
    updated:summariesType
}

export type envStatePair={
    field:"env_state",
    updated:envStateType
}

export type episodicMemoryDescriptionsPair={
    field:"episodic_memory_descriptions",
    updated:episodicMemoryDescriptionsType
}

export type currentFunctionToExecuetePair={
    field:"current_function_to_execuete",
    updated:currentFunctionToExecueteType
}

export type thingsToNotePair={
    field:"things_to_note",
    updated:thingsToNoteType
}

export type listPair=chatHistoryPair|PreviousActionsAndLogsPair|roughPlanToReachGoalPair|summariesPair|envStatePair|
episodicMemoryDescriptionsPair|currentFunctionToExecuetePair|thingsToNotePair

export type anyPair=listPair|stringPair

//requests to send


export type loginRequest=Request<{},{},{
        username:string,
        password:string
}>
export type signUpRequest=loginRequest
export type clickHistoryRequest = Request<{},{},{}>& {
    headers:{
        token:string,
        model:string,
        chat_number:string
    }
}

export type loadHistoryTitlesRequest= Request<{},{},{
    model:string
}>&{
    headers:{
        token:string
    }
}

export type deleteChatRequest=Request<{},{},{}>&{
    headers:{
        token:string,
        model:string,
        chat_number:string
    }
}

export type sendMessageRequest=Request<{},{},{
    message:string,
    model:string,
    chat_number:string
}> &{
    headers:{
        token:string
    }
}

export type updateChatRequest= Request<{},{},{}> &{
    headers:{
        token:string,
        model:string,
        chat_number:string
    }
}

export type loadNewChatRequest=Request<{},{},{
    model:string
}>&{
    headers:{
        token:string
    }
}

export type afterLoginRequest=loadHistoryTitlesRequest|deleteChatRequest|sendMessageRequest|updateChatRequest|loadNewChatRequest
