import { useRef } from "react";
import * as CustomTypes from '../types'
export function useHtmlDivRef():CustomTypes.divRefHookType{
    const divRef=useRef<HTMLDivElement|null>(null)
    function getDivRefCurrent():HTMLDivElement{
        const divRefCurrent=divRef.current
        if(!divRefCurrent){
            throw new Error("div ref is null")
        }
        return divRefCurrent
    }
    return {divRef,getDivRefCurrent}
}