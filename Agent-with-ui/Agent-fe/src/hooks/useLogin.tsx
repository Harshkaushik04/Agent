import { useContext } from "react";
import { loginContext } from "../context/LoginContextProvider";
import * as CustomTypes from '../types'

export function useLogin():CustomTypes.loginContextType{
    const ctx=useContext(loginContext)
    if(!ctx){
        throw new Error("login context doesnt exist")
    }
    return ctx;
}