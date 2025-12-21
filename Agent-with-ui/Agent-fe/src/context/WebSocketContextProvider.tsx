import { useState,createContext,useEffect } from "react";
import * as CustomTypes from "../types"
export const WebSocketContext=createContext<WebSocket|null>(null)

export function WebSocketContextProvider({children}:CustomTypes.props){
    const [socket,setSocket]=useState<WebSocket|null>(null)
    useEffect(()=>{
        setSocket(new WebSocket("ws://localhost:8080"))
        return ()=>socket?.close()
    },[socket])
    return(
        <WebSocketContext.Provider value={socket}>
            {children}
        </WebSocketContext.Provider>
    )
}