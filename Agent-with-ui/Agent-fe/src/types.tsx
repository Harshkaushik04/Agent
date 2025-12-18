import type{ NavigateFunction } from "react-router-dom"
import type { ReactNode } from "react"
export type numString=number|string

//Database-data types
export type messageType={
        role:String,
        content:String,
        before_think:String,
        after_think:String,
        timestamp:Date
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
  messages:messageType[]
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