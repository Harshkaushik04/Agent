import { useRef } from "react";
import * as CustomTypes from '../types'
export function useHtmlTextAreaRef():CustomTypes.textAreaRefHookType{
    const textareaRef=useRef<HTMLTextAreaElement|null>(null)
    function getTextAreaRefCurrent():HTMLTextAreaElement{
        const textAreaRefCurrent=textareaRef.current
        if(!textAreaRefCurrent){
            throw new Error("text area ref is null")
        }
        return textAreaRefCurrent
    }
    return {textareaRef,getTextAreaRefCurrent}
}