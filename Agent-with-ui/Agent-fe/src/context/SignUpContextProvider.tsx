import { useState,createContext } from "react";
import { useNavigate } from "react-router-dom";
import * as CustomTypes from '../types'

export const signUpContext=createContext<CustomTypes.signUpContextType|null>(null)

export function SignUpContextProvider({children}:CustomTypes.props){
    const [username,setUsername]=useState<string>("")
    const [password,setPassword]=useState<string>("")
    const Navigate=useNavigate()
    return(
        <signUpContext.Provider value={{username,setUsername,password,setPassword,Navigate}}>
            {children}
        </signUpContext.Provider>
    )
}