import { useState,createContext } from "react";
import { useNavigate } from "react-router-dom";
import * as CustomTypes from '../types'

export const loginContext=createContext<CustomTypes.loginContextType|null>(null)

export function LoginContextProvider({children}:CustomTypes.props){
    const [username,setUsername]=useState<string>("")
    const [password,setPassword]=useState<string>("")
    const Navigate=useNavigate()
    return(
        <loginContext.Provider value={{username,setUsername,password,setPassword,Navigate}}>
            {children}
        </loginContext.Provider>
    )
}