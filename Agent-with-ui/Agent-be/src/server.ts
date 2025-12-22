import { connectDB, HistoryModel, UserModel } from "./db.js"
import { Request, Response, NextFunction } from 'express';
import express from "express";
import cors from "cors";
import jwt from "jsonwebtoken";
import dotenv from "dotenv";
import axios from "axios"
import WebSocket,{WebSocketServer} from "ws";
import * as CustomTypes from './types.js'
import path from 'path'
import { fileURLToPath } from "url";
import { json } from "stream/consumers";

const wss=new WebSocketServer({port:8080})
let usernameToWebSocket=new Map<string,WebSocket>()
let webSocketToUsername=new Map<WebSocket,string>()
// Recreate __dirname for ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({path:path.resolve(__dirname,'../../.env')})
// Now your existing line will work
// console.log(`dotenv location:${path.resolve(__dirname, '../../.env')}`)
connectDB();
let app=express();

const JWT_SECRET="randomnum1";
const PORT=3000;

let pendingApprovals=new Map<string,(choice:boolean)=>void>
async function requestApprovalStateAndUpdation(ws: WebSocket, username: string, state:CustomTypes.workingMemorySchemaType,
    stateUpdationObject:CustomTypes.stateUpdationType[]
): Promise<boolean> {
    // const state_string=JSON.stringify(state)
    // const state_updation_string=JSON.stringify(stateUpdationObject)
    ws.send(JSON.stringify({
        eventType: "approval",
        state:state,
        stateUpdationObject:stateUpdationObject
    }));
    return new Promise((resolve) => {
        pendingApprovals.set(username, resolve);
    });
}

async function requestApprovalState(ws: WebSocket, username: string, state:CustomTypes.workingMemorySchemaType): Promise<boolean> {
    // const state_string=JSON.stringify(state)
    // const state_updation_string=JSON.stringify(stateUpdationObject)
    ws.send(JSON.stringify({
        eventType: "approval",
        state:state
    }));
    return new Promise((resolve) => {
        pendingApprovals.set(username, resolve);
    });
}

// function sendOutput(ws:WebSocket,username:string)
let approved=false
let feedback=""
wss.on("connection",function(ws:WebSocket){
    console.log("new user connected")
    ws.on("message",(msg:WebSocket.RawData)=>{
        const json_message:CustomTypes.wsToBackend=JSON.parse(msg.toString())
        let decryptedData:CustomTypes.jwtDecrypted
        try {
            decryptedData = jwt.verify(json_message.token as string, JWT_SECRET) as CustomTypes.jwtDecrypted;
        } catch (err) {
            throw new Error("[server.ts]WebSocket Check: wrong jwt token")
        }
        const username=decryptedData.username
        if(!usernameToWebSocket.get(username)){
            console.log(`username:${username} websocket registered`)
            usernameToWebSocket.set(username,ws)
            webSocketToUsername.set(ws,username)
        }
        if(json_message.eventType=="approval"){
            const resolve=pendingApprovals.get(username)
            if(!resolve){
                throw new Error(`[server.ts] No pending approvals from username ${username}`)
            }
            if(json_message.approval=="yes"){
                approved=true
            }
            else{
                approved=false
                feedback=json_message?.feedback?json_message.feedback:""
            }
            resolve(json_message.approval=="yes")
            pendingApprovals.delete(username)
        }
    })
})

app.use(express.json());
app.use(cors({
    "origin":"http://localhost:5173"
}));

function authMiddleware(req:Request,res:Response,next:NextFunction){
    // const custom_req=req as CustomTypes.afterLoginRequest
    // const custom_res=res as Response<CustomTypes.anyResponseType>
    if(!req.headers.token){
        console.log(`hi:`,req.headers.token)
        return res.json({
            valid:false
        });
    }
    else{
        try {
            const rawDecryptedData = jwt.verify(req.headers.token as string, JWT_SECRET);
            const decryptedData=rawDecryptedData as CustomTypes.jwtDecrypted;
            //@ts-ignore
            req.decrypted_username = decryptedData.username; 
            //@ts-ignore
            console.log(`req.decrypted_username:`,req.decrypted_username)
            next();
        } catch (err) {
            console.log("err:",err)
            console.log(`hi2`)
            return res.json({
                valid:false
            });
        }
    }
}

app.post("/signup",async (req:CustomTypes.signUpRequest,res:Response<CustomTypes.signUpType>)=>{
    let username:string=req.body.username;
    let password:string=req.body.password;
    let user=await UserModel.findOne({
        username:username
    })
    if(user){
        return res.json({
            whetherDuplicate:true
        })
    }
    // PROXY_MODEL,username,PROXY_TITLE---->num_chats already created
    await HistoryModel.create({
        username:username,
        model:process.env.PROXY_MODEL,
        title:process.env.PROXY_TITLE,
        messages:[{"role":"system","content":"0"}]
    })
    //username not taken=>make new id
    await UserModel.create({
        username:username,
        password:password
    })
    return res.json({
        whetherDuplicate:false
    })
})

app.post("/login",async (req:CustomTypes.loginRequest,res:Response<CustomTypes.loginType>)=>{
    let username:string=req.body.username;
    let password:string=req.body.password;
    let user=await UserModel.findOne({
        username:username,
        password:password
    });
    if(!user) {return res.json({
        valid:false
    })}
    // PROXY_MODEL,username,PROXY_TITLE---->num_chats already created
    console.log(`title:${process.env.PROXY_TITLE}`)
    let chat_row=await HistoryModel.findOne({
        username:username,
        model:process.env.PROXY_MODEL,
        title:process.env.PROXY_TITLE
    })
    if(!chat_row){
        throw new Error("[server.ts] chat number row in HistoryModel does not exist")
    }
    let num_chats:number=0;
    num_chats=Number(chat_row.messages[0].content);
    chat_row.messages[0].content = String(num_chats + 1);
    await chat_row.save();
    if(user){
        let jwt_token=jwt.sign({
            "username":username
        },JWT_SECRET);
        return res.json({
            username:username,
            token:jwt_token,
            valid:true
        })
    }
})

app.use(authMiddleware);
app.post("/load-history-titles",async (req:Request,res:Response)=>{
    // const custom_res=res as Response<CustomTypes.loadHistoryTitlesType>
    // const custom_req=req as CustomTypes.loadHistoryTitlesRequest
    //@ts-ignore
    let username:string=req.decrypted_username;
    let model:string=req.body.model;
    let historyTitles=await HistoryModel.find({
        username:username,
        model:model
    },"title");
    let len:number=historyTitles.length;
    let titlesList:string[]=[]
    for(let i=0;i<len;i++){
        let custom_title=historyTitles[i]["title"]
        if(!custom_title){
            throw new Error("historyTitles[i]['title'] doesnt exist")
        }
        titlesList.push(custom_title);
    }
    return res.json({
        valid:true,
        titles:titlesList
    })
})

app.post("/load-new-chat",async (req:Request,res:Response)=>{
    console.log(`[load-new-chat] request recieved`)
    // const custom_req=req as CustomTypes.loadNewChatRequest
    // const custom_res=res as Response<CustomTypes.loadNewChatType>
    //@ts-ignore
    let username:string=req.decrypted_username;
    let model:string=req.body.model;
    // PROXY_MODEL,username,PROXY_TITLE---->num_chats already created
    let chat_row=await HistoryModel.findOne({
        username:username,
        model:process.env.PROXY_MODEL,
        title:process.env.PROXY_TITLE
    })
    if(!chat_row){
        throw new Error("chat number row in HistoryModel does not exist")
    }
    let num_chats:number=Number(chat_row.messages[0].content);
    await HistoryModel.create({
        username:username,
        model:model,
        title:`title${num_chats+1}`
    })
    chat_row.messages[0].content = String(num_chats + 1);
    console.log(`[load-new-chat] chat_row.messages[0].content:${chat_row.messages[0].content}`)
    await chat_row.save();
    return res.json({
        valid:true,
        chat_number:num_chats+1
    })
})

app.get("/update-chat",async (req:Request,res:Response)=>{
    console.log(`[update-chat] entered request`)
    // const custom_req=req as CustomTypes.updateChatRequest
    // const custom_res=res as Response<CustomTypes.updateChatType>
    //@ts-ignore
    let username:string=req.decrypted_username;
    let model:string=String(req.headers.model);
    let chat_number:number=Number(req.headers.chat_number);
    let user=await HistoryModel.findOne({
        username:username,
        model:model,
        title:`title${chat_number}`
    })
    console.log(`[update-chat] username:${username},model:${model},title:title${chat_number}`)
    return res.json({
        valid:true,
        value_json:(user?.messages ? user.messages : [])
    })
})

app.get("/click-history",async (req:Request,res:Response)=>{
    console.log(`[click-history] entered request`)
    // const custom_req=req as CustomTypes.clickHistoryRequest
    // const custom_res=res as Response<CustomTypes.clickHistoryType>
    //@ts-ignore
    let username:string=req.decrypted_username;
    let model:string=String(req.headers.model);
    let chat_number:number=Number(req.headers.chat_number);
    console.log(`[click-history]username:${username} model:${model} title:title${chat_number}`)
    let user=await HistoryModel.findOne({
        username:username,
        model:model,
        title:`title${chat_number}`
    })
    console.log(`user.messages:${user?.messages}`)
    return res.json({
        valid:true,
        value_json:(user?.messages ? user.messages:[])
    })
})

app.delete("/delete-chat",async (req:Request,res:Response)=>{
    console.log(`[delete-chat] entered request`)
    // const custom_req=req as CustomTypes.deleteChatRequest
    // const custom_res=res as Response<CustomTypes.deleteChatType>
    //@ts-ignore
    let username:string=req.decrypted_username;
    let model:string=String(req.headers.model);
    let chat_number:number=Number(req.headers.chat_number);
    await HistoryModel.deleteOne({
        username:username,
        model:model,
        title:`title${chat_number}`
    })
    return res.json({
        valid:true,
        chat_number:-1
    })
})

app.post("/send-message",async (req:Request,res:Response)=>{
    console.log(`[send-message]request arrived`)
    // const custom_req=req as CustomTypes.sendMessageRequest
    // const custom_res=res as Response<CustomTypes.sendMessageType>
    //@ts-ignore
    let username:string=req.decrypted_username;
    let user_message:string=req.body.message;
    let model:string=req.body.model;
    let chat_number:number=Number(req.body.chat_number);
    let state:CustomTypes.workingMemorySchemaType=initialiseWorkingMemory(user_message)
    const foundWs:WebSocket|undefined=usernameToWebSocket.get(username)
    if(!foundWs){
        throw new Error("[server.ts] websocket not connected till now!! => connect message not received?")
    }
    //to complete: implementation of feedback,approval by user
    let resp:Axios.AxiosXHR<CustomTypes.stateObjectType>
    while(!approved){
        feedback=""
        resp=await axios.post<CustomTypes.stateObjectType>("http://localhost:5000/generate-working-memory",{
            state:state,
            feedback:feedback,
            model:model,
            chat_number:chat_number
        })
        await requestApprovalState(foundWs,username,state)
    }
    //@ts-ignore
    state=resp.data.state
    approved=false
    let stateUpdateObj:CustomTypes.stateUpdationType[]=[]
    let log=""
    while(!state.final_goal_completed){
        while(!approved){
            feedback=""
            let resp1=await axios.post<CustomTypes.resoningResponseType>("http://localhost:5000/reasoning",{
                state:state,
                feedback:feedback,
                model:model,
                chat_number:chat_number
            })
            stateUpdateObj=resp1.data.stateUpdationObject
            await requestApprovalStateAndUpdation(foundWs,username,state,stateUpdateObj)
        }
        updateState(state,stateUpdateObj)
        approved=false
        while(!approved){
            feedback=""
            let resp2=await axios.post<CustomTypes.execueteResponseType>("http://localhost:5000/execuete",{
                state:state,
                model:model,
                chat_number:chat_number,
                feedback:feedback
            })
            log=resp2.data.log
            stateUpdateObj=resp2.data.stateUpdationObject
            await requestApprovalStateAndUpdation(foundWs,username,state,stateUpdateObj)
        }
        updateState(state,stateUpdateObj)
        approved=false
        while(!approved){
            feedback=""
            let resp3=await axios.post<CustomTypes.makeLogResponseType>("http://localhost:5000/make-log",{
                state:state,
                log:log,
                feedback:feedback,
                model:model,
                chat_number:chat_number
            })
            stateUpdateObj=resp3.data.stateUpdationObject
            await requestApprovalStateAndUpdation(foundWs,username,state,stateUpdateObj)
        }
        updateState(state,stateUpdateObj)
        approved=false
        while(!approved){
            feedback=""
            let resp4=await axios.post<CustomTypes.updateWorkingMemoryResponseType>("http://localhost:5000/update-working-memory",{
                state:state,
                feedback:feedback,
                model:model,
                chat_number:chat_number
            })
            stateUpdateObj=resp4.data.stateUpdationObject
            await requestApprovalStateAndUpdation(foundWs,username,state,stateUpdateObj)
        }
        updateState(state,stateUpdateObj)
        approved=false
    }
    //generate-working-memory
    //while-loop-start{
    //reasoning
    //execuete
    //make-log
    //update-working-memory
    //while-loop-end}
    return res.json({
        valid:true
    })
})

function initialiseWorkingMemory(user_message:string):CustomTypes.workingMemorySchemaType{
    const state:CustomTypes.workingMemorySchemaType={
        chat_history:[{
            serial_number:0,
            role:"user",
            content:user_message
        }],
        previous_actions_and_logs:[],
        final_goal:user_message,
        current_goal:"reasoning to make a plan",
        rough_plan_to_reach_goal:[],
        summaries:[],
        env_state:[],
        episodic_memory_descriptions:[],
        current_function_to_execuete:{
            function_name:"",
            inputs:{}
        },
        things_to_note:[],
        final_goal_completed:false
    }
    return state
}
function isListFieldType(x: string): x is CustomTypes.listFieldType {
  return CustomTypes.listFieldValues.includes(x as CustomTypes.listFieldType);
}
function isStringFieldType(x: string): x is CustomTypes.listFieldType {
  return CustomTypes.stringFieldValues.includes(x as CustomTypes.stringFieldType);
}
//to complete
function updateState(state:CustomTypes.workingMemorySchemaType,state_updation_object:CustomTypes.stateUpdationType[]){
    for(const upd of state_updation_object){
        if(upd.updateType=="delete"){
            if (isListFieldType(upd.field)) {
                const arr = state[upd.field];
                if (!Array.isArray(arr)) {
                    throw new Error(`Field ${upd.field} is not an array`);
                }
                arr.splice(upd.serial_number, 1);
            }
            else if (isStringFieldType(upd.field)) {
                // @ts-ignore
                state[upd.field] = "";
            }
        }
        else if(upd.updateType=="add"){
            if(isListFieldType(upd.field)){
                const arr=state[upd.field]
                if(!Array.isArray(arr)){
                    throw new Error(`Field ${upd.field} is not an array`)
                }
                //@ts-ignore
                arr.push(upd.updated)
            }
            else if(isStringFieldType(upd.field)){
                //@ts-ignore
                state[upd.field] = upd.updated
            }
        }
        else if(upd.updateType=="update"){
            if(isListFieldType(upd.field)){
                const arr=state[upd.field]
                if(!Array.isArray(arr)){
                    throw new Error(`Field ${upd.field} is not an array`)
                }
                //@ts-ignore
                arr[upd.serial_number]=upd.updated
            }
            else if(isStringFieldType(upd.field)){
                //@ts-ignore
                state[upd.field]=upd.updated
            }
        }
    }
    return state
}

app.listen(PORT,()=>{
    console.log(`server listening at port ${PORT}`)
})