import { useState,createContext } from "react";
import { useNavigate } from "react-router-dom";
import * as CustomTypes from '../types'

export let ChatContext=createContext<CustomTypes.chatContextType|null>(null)

export function ChatContextProvider({children}:CustomTypes.props){
    const [historyTitles,setHistoryTitles]=useState<string[]>([]);
    const [historyChat,setHistoryChat]=useState<CustomTypes.messageType[]>([])
    const [extraContent,setExtraContent]=useState<CustomTypes.ApprovalMessageType[]>([])
    const Navigate=useNavigate();
    return(
        <ChatContext.Provider value={{historyTitles,setHistoryTitles,historyChat,setHistoryChat,extraContent,setExtraContent,Navigate}}>
            {children}
        </ChatContext.Provider>
    )
}
