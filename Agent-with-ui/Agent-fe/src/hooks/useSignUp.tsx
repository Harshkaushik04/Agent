import { useContext } from "react";
import { signUpContext } from "../context/SignUpContextProvider";
import * as CustomTypes from '../types'

export function useSignUp():CustomTypes.signUpContextType{
    const ctx=useContext(signUpContext)
    if(!ctx){
        throw new Error("signUp context doesnt exist")
    }
    return ctx;
}