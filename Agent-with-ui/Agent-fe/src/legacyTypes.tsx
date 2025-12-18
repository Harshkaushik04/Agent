import type { NavigateFunction } from "react-router-dom"

export type numString=number|string

export type messageType={
        role:String,
        content:String,
        before_think:String,
        after_think:String,
        timestamp:Date
}
export interface mainBarLegacy{
  width1:numString,
  height1:numString,
  width2:numString,
  height2:numString,
  content:messageType[],
  setHistoryChat:React.Dispatch<React.SetStateAction<messageType[]>>,
  Navigate:NavigateFunction
}

export interface searchBarLegacy{
  placeholder:string,
  width:numString,
  height:numString,
  historyChat:messageType[],
  setHistoryChat:React.Dispatch<React.SetStateAction<messageType[]>>,
  Navigate:NavigateFunction
}

export interface boxLegacy{
  title:string,
  color:numString,
  setHistoryChat:React.Dispatch<React.SetStateAction<messageType[]>>,
  Navigate:NavigateFunction,
  setHistoryTitles:React.Dispatch<React.SetStateAction<string[]>>
}

export interface sideBarLegacy{
  width:numString,
  height:numString,
  titles:string[],
  setHistoryChat:React.Dispatch<React.SetStateAction<messageType[]>>,
  Navigate:NavigateFunction,
  setHistoryTitles:React.Dispatch<React.SetStateAction<string[]>>
}
