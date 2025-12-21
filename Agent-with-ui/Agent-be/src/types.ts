import { Request } from "express"
import { IncomingHttpHeaders } from "http"
import { JwtPayload } from "jsonwebtoken"
export type numString=number|string

//Database-data types
export type messageType={
        role:String,
        content:String,
        before_think:String,
        after_think:String,
        timestamp:Date
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
export type loginType=i_loginType|invalidResponseType
export type signUpType=i_signUpType
export type anyResponseType=loadHistoryTitlesType|loadNewChatType|deleteChatType|clickHistoryType|updateChatType|sendMessageType|loginType|signUpType

export type loginRequest=Request<{},{},{
        username:string,
        password:string
}>
export type signUpRequest=loginRequest
export type clickHistoryRequest = Request<{},{},{
      decrypted_username:string
}>& {
    headers:{
        token:string,
        model:string,
        chat_number:string
    }
}

export type loadHistoryTitlesRequest= Request<{},{},{
    model:string,
    decrypted_username:string
}>&{
    headers:{
        token:string
    }
}

export type deleteChatRequest=Request<{},{},{
    decrypted_username:string
}>&{
    headers:{
        token:string,
        model:string,
        chat_number:string
    }
}

export type sendMessageRequest=Request<{},{},{
    message:string,
    model:string,
    chat_number:string,
    decrypted_username:string
}> &{
    headers:{
        token:string
    }
}

export type updateChatRequest= Request<{},{},{
    decrypted_username:string
}> &{
    headers:{
        token:string,
        model:string,
        chat_number:string
    }
}

export type loadNewChatRequest=Request<{},{},{
    model:string,
    decrypted_username:string
}>&{
    headers:{
        token:string
    }
}

export type afterLoginRequest=loadHistoryTitlesRequest|deleteChatRequest|sendMessageRequest|updateChatRequest|loadNewChatRequest

export interface jwtDecrypted extends JwtPayload{
    username:string
} 

export type historySchemaType={
    username:string,
    model:string,
    title:string,
    messages:[{
        role:string,
        content:string,
        before_think:string,
        after_think:string,
        timestamp:Date
    }],
    summaries:[
        {
            description:string,
            content:string
        }
    ]
}

export type userSchemaType={
    username:string,
    password:string
}

export type episodicMemorySchemaType={
    username:String,
    title:String,
    memories:[{
        description:String,
        content:String
    }]
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
    brief_expected_outputs:{
        [key:string]:string
    },
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
envStateType|episodicMemoryDescriptionsType|currentFunctionToExecueteType|thingsToNoteType

export type anyFieldType="chat_history"|"previous_actions_and_logs"|"final_goal"|"current_goal"|
"rough_plan_to_reach_goal"|"summaries"|"env_state"|"episodic_memory_descriptions"|
"current_function_to_execuete"|"things_to_note"

export type workingMemorySchemaType={
    chat_history:chatHistoryType[],
    previous_actions_and_logs:addPreviousActionsAndLogsType[],
    final_goal:string,
    current_goal:string,
    rough_plan_to_reach_goal:roughPlanToReachGoalType[],
    summaries:summariesType[],
    env_state:envStateType[],
    episodic_memory_descriptions:episodicMemoryDescriptionsType[],
    current_function_to_execute:currentFunctionToExecueteType,
    things_to_note:thingsToNoteType[],
    final_goal_completed:boolean
}

export type Message={
    role:string,
    content:string,
    before_think:string,
    after_think:string
}

export type generateModelRequest=Request<{},{},{
    working_memory:workingMemorySchemaType
}>


//generate-working-memory
//while-loop-start{
//reasoning
//execuete
//make-log
//update-working-memory
//while-loop-end}

export type wsToFrontend_approval={ 
    eventType:"approval",
    message:string
}
export type wsToFrontend_showOutput={
    eventType:"showOutput",
    message:string
}

export type wsToFrontend=wsToFrontend_approval|wsToFrontend_showOutput
export type wsToBackend_approval={
    eventType:"approval",
    message:string,
    token:string
}
export type wsToBackend_connect={
  eventType:"connect",
  token:string
}
export type wsToBackend=wsToBackend_approval|wsToBackend_connect

//state updation 
// for fields function_to_execuete,current_goal,final_goal => serial_number=0
export type deleteAnyType={
    updateType:"delete",
    field:string,
    serial_number:number
}

export type addAnyType={
    updateType:"add",
    field:anyFieldType,
    updated:anyUpdateType
}

export type updateAnyType={
    updateType:"update",
    field:anyFieldType,
    serial_number:number,
    updated:anyUpdateType
}

export type stateUpdationType=deleteAnyType|addAnyType|updateAnyType
export type stateObjectType={
    state:workingMemorySchemaType
}
export type stateUpdationObjectType={
    stateUpdationObject:stateUpdationType[]
}

export type resoningResponseType={
    before_think:string,
    stateUpdationObject:stateUpdationType[]
}

export type execueteResponseType={
    log:string,
    stateUpdationObject:stateUpdationType[]
}

export type makeLogResponseType={
    stateUpdationObject:stateUpdationType[]
}

export type updateWorkingMemoryResponseType={
    stateUpdationObject:stateUpdationType[]
}