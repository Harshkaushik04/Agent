import { WebSocketContext} from "../context/WebSocketContextProvider";
import { useContext } from "react";

export function useWebSocket(){
    const socket=useContext(WebSocketContext)
    if(!socket){
        throw new Error("[useWebSocket.tsx]socket not connected")
    }
    return socket
}