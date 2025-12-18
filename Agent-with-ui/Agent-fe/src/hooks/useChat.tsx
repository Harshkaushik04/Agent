import { useContext } from "react";
import { ChatContext } from "../context/ChatContextProvider";
import * as CustomTypes from '../types'
export function useChat():CustomTypes.chatContextType{
    const context=useContext(ChatContext)
    if(!context){
        throw new Error("chat context is of null type")
    }
    return context;
}
