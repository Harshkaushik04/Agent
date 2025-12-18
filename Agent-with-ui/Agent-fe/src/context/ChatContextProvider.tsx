import { useState,createContext } from "react";
import { useNavigate } from "react-router-dom";
import * as CustomTypes from '../types'

export let ChatContext=createContext<CustomTypes.chatContextType|null>(null)

export function ChatContextProvider({children}:CustomTypes.props){
    const [historyTitles,setHistoryTitles]=useState<string[]>([]);
    const [historyChat,setHistoryChat]=useState<CustomTypes.messageType[]>([])
    const Navigate=useNavigate();
    return(
        <ChatContext.Provider value={{historyTitles,setHistoryTitles,historyChat,setHistoryChat,Navigate}}>
            {children}
        </ChatContext.Provider>
    )
}
