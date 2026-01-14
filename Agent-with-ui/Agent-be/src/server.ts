import { connectDB, HistoryModel, UserModel,EpisodicMemoryModel,CompleteHistoryModel,WorkingMemoryModel,EpisodicMemoryDescriptionsModel } from "./db.js"
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
import mongoose,{HydratedDocument} from "mongoose"

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
    stateUpdationObject:CustomTypes.stateUpdationType[],role:string
): Promise<boolean> {
    // const state_string=JSON.stringify(state)
    // const state_updation_string=JSON.stringify(stateUpdationObject)
    console.log(`[requestApprovalStateAndUpdation] sending approval message to frontend`)
    try{
        ws.send(JSON.stringify({
            eventType: "approval",
            state:state,
            stateUpdationObject:stateUpdationObject,
            role:role
        }));
    }
    catch(e){
        console.log(`Error:${e}`)
    }
    return new Promise((resolve) => {
        pendingApprovals.set(username, resolve);
    });
}

async function updateCompleteHistoryWithOnlyStateUpdationObjectAndRequestApprovalStateAndUpdation(ws:WebSocket,
    username:string,state:CustomTypes.workingMemorySchemaType,
    stateUpdationObject:CustomTypes.stateUpdationType[],
    userCompleteHistory:HydratedDocument<CustomTypes.completeHistorySchemaType>,role:string
){
    //==========================================
    userCompleteHistory.messages.push({
        role:role,
        content:JSON.stringify(stateUpdationObject),
        messageType:"approvalPending",
        timestamp:new Date()
    })
    await userCompleteHistory.save()
    //==========================================
    await requestApprovalStateAndUpdation(ws,username,state,stateUpdationObject,role)
    //==========================================
    if(approved){
        let temp_len:number=userCompleteHistory.messages.length
        userCompleteHistory.messages[temp_len-1].messageType="approvalYes"
        await userCompleteHistory.save()
    }
    else{
        let temp_len:number=userCompleteHistory.messages.length
        userCompleteHistory.messages[temp_len-1].messageType="approvalNo"
        await userCompleteHistory.save()
    }
    //==========================================
}


async function updateCompleteHistoryWithStateUpdationObjectAndLogAndRequestApprovalStateAndUpdation(ws:WebSocket,
    username:string,state:CustomTypes.workingMemorySchemaType,
    stateUpdationObject:CustomTypes.stateUpdationType[],log:string,
    userCompleteHistory:HydratedDocument<CustomTypes.completeHistorySchemaType>,role:string
){
    //==========================================
    let content=JSON.stringify(stateUpdationObject)+"\n"+"log: "+log
    userCompleteHistory.messages.push({
        role:role,
        content:content,
        messageType:"approvalPending",
        timestamp:new Date()
    })
    await userCompleteHistory.save()
    //==========================================
    await requestApprovalStateAndUpdation(ws,username,state,stateUpdationObject,role)
    //==========================================
    if(approved){
        let temp_len:number=userCompleteHistory.messages.length
        userCompleteHistory.messages[temp_len-1].messageType="approvalYes"
        await userCompleteHistory.save()
    }
    else{
        let temp_len:number=userCompleteHistory.messages.length
        userCompleteHistory.messages[temp_len-1].messageType="approvalNo"
        await userCompleteHistory.save()
    }
    //==========================================
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

// function stateWithUserToState(stateWithUser:HydratedDocument<CustomTypes.workingMemoryWithUserSchemaType>):CustomTypes.workingMemorySchemaType{
//     let state:CustomTypes.workingMemorySchemaType={
//         chat_history:stateWithUser.chat_history,
//         previous_actions_and_logs: stateWithUser.previous_actions_and_logs,
//         final_goal: stateWithUser.final_goal,
//         current_goal: stateWithUser.current_goal,
//         rough_plan_to_reach_goal: stateWithUser.rough_plan_to_reach_goal,
//         variables:stateWithUser.variables,
//         env_state: stateWithUser.env_state,
//         episodic_memory_descriptions: stateWithUser.episodic_memory_descriptions,
//         current_function_to_execuete: stateWithUser.current_function_to_execuete,
//         things_to_note: stateWithUser.things_to_note,
//         final_goal_completed: stateWithUser.final_goal_completed
//     }
//     return state
// }

function stateWithUserToState(stateWithUser: HydratedDocument<CustomTypes.workingMemoryWithUserSchemaType>): CustomTypes.workingMemorySchemaType {
    
    // Helper to convert Mongoose Maps to plain Objects (fixes "inputs: {}" bug)
    const mapToObject = (map: any) => {
        if (map instanceof Map) return Object.fromEntries(map);
        if (typeof map === 'object' && map !== null) return map;
        return {};
    };

    let state: CustomTypes.workingMemorySchemaType = {
        // 1. Simple Strings (Direct copy)
        final_goal: stateWithUser.final_goal,
        current_goal: stateWithUser.current_goal,
        final_goal_completed: stateWithUser.final_goal_completed,

        // 2. Arrays: Map and reconstruct to remove _id
        chat_history: stateWithUser.chat_history.map(chat => ({
            serial_number: chat.serial_number,
            role: chat.role,
            content: chat.content
        })),

        previous_actions_and_logs: stateWithUser.previous_actions_and_logs.map(action => ({
            serial_number: action.serial_number,
            description: action.description,
            function_name: action.function_name,
            inputs: mapToObject(action.inputs), // Convert Map -> Object
            outputs: mapToObject(action.outputs),
            log: action.log,
            filter_words: action.filter_words
        })),

        rough_plan_to_reach_goal: stateWithUser.rough_plan_to_reach_goal.map(plan => ({
            serial_number: plan.serial_number,
            description: plan.description,
            function_name: plan.function_name,
            inputs: mapToObject(plan.inputs),   // Convert Map -> Object
            brief_expected_outputs: plan.brief_expected_outputs,
            status: plan.status
        })),

        variables: stateWithUser.variables.map(variable => ({
            serial_number: variable.serial_number,
            variable_type: variable.variable_type,
            description: variable.description,
            content: variable.content,
            filter_words: variable.filter_words
        })),

        env_state: stateWithUser.env_state.map(env => ({
            serial_number: env.serial_number,
            description: env.description,
            content: env.content
        })),

        episodic_memory_descriptions: stateWithUser.episodic_memory_descriptions.map(mem => ({
            serial_number: mem.serial_number,
            description: mem.description
        })),

        things_to_note: stateWithUser.things_to_note.map(note => ({
            serial_number: note.serial_number,
            description: note.description,
            content: note.content
        })),

        // 3. Single Nested Object
        current_function_to_execuete: {
            function_name: stateWithUser.current_function_to_execuete?.function_name || "",
            inputs: mapToObject(stateWithUser.current_function_to_execuete?.inputs)
        }
    };

    return state;
}

async function saveStateToStateWithUser(state:CustomTypes.workingMemorySchemaType,stateWithUser:HydratedDocument<CustomTypes.workingMemoryWithUserSchemaType>){
    stateWithUser.chat_history=state.chat_history
    stateWithUser.previous_actions_and_logs=state.previous_actions_and_logs
    stateWithUser.final_goal=state.final_goal
    stateWithUser.current_goal=state.current_goal
    stateWithUser.rough_plan_to_reach_goal=state.rough_plan_to_reach_goal
    stateWithUser.variables=state.variables
    stateWithUser.env_state=state.env_state
    stateWithUser.episodic_memory_descriptions=state.episodic_memory_descriptions
    stateWithUser.current_function_to_execuete=state.current_function_to_execuete
    stateWithUser.things_to_note=state.things_to_note
    stateWithUser.final_goal_completed=state.final_goal_completed
    await stateWithUser.save()
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
        usernameToWebSocket.set(username,ws)
        webSocketToUsername.set(ws,username)
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
// app.use(cors({
//     "origin":"http://localhost:5173"
// }));

app.use(cors())
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
    await CompleteHistoryModel.create({
        username:username,
        model:model,
        title:`title${num_chats+1}`
    })
    await WorkingMemoryModel.create({
        username:username,
        model:model,
        title:`title${num_chats+1}`,
        chat_history:[],
        previous_actions_and_logs:[],
        final_goal:"",
        current_goal:"",
        rough_plan_to_reach_goal:[],
        variables:[],
        env_state:[],
        episodic_memory_descriptions:[],
        current_function_to_execuete:{
            function_name:"",
            inputs:{}
        },
        things_to_note:[],
        final_goal_completed:"yes"
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
    let user=await CompleteHistoryModel.findOne({
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
    let user=await CompleteHistoryModel.findOne({
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
    await CompleteHistoryModel.deleteOne({
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
    let stateWithUser:HydratedDocument<CustomTypes.workingMemoryWithUserSchemaType>|null=await WorkingMemoryModel.findOne({
        username:username,
        model:model,
        title:`title${chat_number}`
    })
    let state:CustomTypes.workingMemorySchemaType
    if(!stateWithUser){
        console.log("why is stateWithUser not defined till now?")
        await WorkingMemoryModel.create({
            username:username,
            model:model,
            title:`title${chat_number}`,
            chat_history:[{
                serial_number:0,
                role:"user",
                content:user_message
            }],
            previous_actions_and_logs:[],
            final_goal:user_message,
            current_goal:"",
            rough_plan_to_reach_goal:[],
            variables:[],
            env_state:[],
            episodic_memory_descriptions:[],
            current_function_to_execuete:{
                function_name:"",
                inputs:{}
            },
            things_to_note:[],
            final_goal_completed:"no"
        })
        stateWithUser=await WorkingMemoryModel.findOne({
            username:username,
            model:model,
            title:`title${chat_number}`
        })
        if(!stateWithUser){
            throw new Error("why is stateWithUser still not defined??")
        }
        state=stateWithUserToState(stateWithUser)
    }
    else{
        state=stateWithUserToState(stateWithUser)
        let len_chat:number=state.chat_history.length
        let serial_num:number=1
        if(len_chat!=0){
            serial_num=state.chat_history[len_chat-1].serial_number+1
        }
        state.chat_history.push({
            serial_number:serial_num,
            role:"user",
            content:user_message
        })
        saveStateToStateWithUser(state,stateWithUser)
    }
    let userCompleteHistory=await CompleteHistoryModel.findOne({
        username:username,
        model:model,
        title:`title${chat_number}`
    })
    if(!userCompleteHistory){
        await CompleteHistoryModel.create({
            username:username,
            model:model,
            title:`title${chat_number}`,
            messages:[{
                role:"user",
                content:user_message,
                messageType:"normal",
                timestamp:new Date()
            }]
        })
        userCompleteHistory=await CompleteHistoryModel.findOne({
            username:username,
            model:model,
            title:`title${chat_number}`
        })
        if(!userCompleteHistory){
            throw new Error("entry just made, so this error is technically not possible")
        }
    }
    else{
        userCompleteHistory.messages.push({
            role:"user",
            content:user_message,
            messageType:"normal",
            timestamp:new Date()
        })
        await userCompleteHistory.save()
    }
    const userHistory=await HistoryModel.findOne({
        username:username,
        model:model,
        title:`title${chat_number}`
    })
    if(!userHistory){
        throw new Error("why is userHistory not defined")
    }
    userHistory.messages.push({
        role:"user",
        content:user_message,
        before_think:"",
        after_think:"",
        timestamp:new Date()
    })
    await userHistory.save()
    const foundWs:WebSocket|undefined=usernameToWebSocket.get(username)
    if(!foundWs){
        throw new Error("[server.ts] websocket not connected till now!! => connect message not received?")
    }
    //to complete: implementation of feedback,approval by user
    let resp:Axios.AxiosXHR<CustomTypes.stateUpdationObjectType>
    let stateUpdateObj:CustomTypes.stateUpdationType[]=[]
    feedback=""
    approved=false
    while(!approved){
        // console.log("request:")
        // console.log("state:",state)
        // console.log("feedback:",feedback)
        // console.log("model:",model)
        // console.log("chat_number:",chat_number)
        resp=await axios.post<CustomTypes.stateUpdationObjectType>("http://localhost:5000/generate-working-memory",{
            state:state,
            feedback:feedback,
            model:model,
            chat_number:chat_number
        })
        stateUpdateObj=resp.data.stateUpdationObject
        await updateCompleteHistoryWithOnlyStateUpdationObjectAndRequestApprovalStateAndUpdation(foundWs,username,state,stateUpdateObj,
            userCompleteHistory,"generate-working-memory")
    }
    console.log(`stateUpdateObj:`,stateUpdateObj)
    console.log(`old state:`,state)
    state=updateState(state,stateUpdateObj)
    console.log(`state updated to:`,state)
    saveStateToStateWithUser(state,stateWithUser)
    let log=""
    while(state.final_goal_completed!="yes"){
        feedback=""
        approved=false
        while(!approved){
            let resp1=await axios.post<CustomTypes.resoningResponseType>("http://localhost:5000/reasoning",{
                state:state,
                feedback:feedback,
                model:model,
                chat_number:chat_number
            })
            stateUpdateObj=resp1.data.stateUpdationObject
            await updateCompleteHistoryWithOnlyStateUpdationObjectAndRequestApprovalStateAndUpdation(foundWs,username,state,stateUpdateObj,
            userCompleteHistory,"reasoning")
        }
        state=updateState(state,stateUpdateObj)
        console.log(`state updated to:`,state)
        saveStateToStateWithUser(state,stateWithUser)
        approved=false
        feedback=""
        while(!approved){
            let resp2=await axios.post<CustomTypes.execueteResponseType>("http://localhost:5000/execuete",{
                state:state,
                model:model,
                chat_number:chat_number,
                feedback:feedback
            })
            log=resp2.data.log
            stateUpdateObj=resp2.data.stateUpdationObject
            await updateCompleteHistoryWithStateUpdationObjectAndLogAndRequestApprovalStateAndUpdation(foundWs,username,state,stateUpdateObj,
            log,userCompleteHistory,"make-log")
        }
        state=updateState(state,stateUpdateObj)
        console.log(`state updated to:`,state)
        saveStateToStateWithUser(state,stateWithUser)
        approved=false
        feedback=""
        while(!approved){
            let resp3=await axios.post<CustomTypes.makeLogResponseType>("http://localhost:5000/make-log",{
                state:state,
                log:log,
                feedback:feedback,
                model:model,
                chat_number:chat_number
            })
            stateUpdateObj=resp3.data.stateUpdationObject
            await updateCompleteHistoryWithOnlyStateUpdationObjectAndRequestApprovalStateAndUpdation(foundWs,username,state,stateUpdateObj,
            userCompleteHistory,"make-log")
        }
        state=updateState(state,stateUpdateObj)
        console.log(`state updated to:`,state)
        saveStateToStateWithUser(state,stateWithUser)
        approved=false
        feedback=""
        while(!approved){
            let resp4=await axios.post<CustomTypes.updateWorkingMemoryResponseType>("http://localhost:5000/update-working-memory",{
                state:state,
                feedback:feedback,
                model:model,
                chat_number:chat_number
            })
            stateUpdateObj=resp4.data.stateUpdationObject
            await updateCompleteHistoryWithOnlyStateUpdationObjectAndRequestApprovalStateAndUpdation(foundWs,username,state,stateUpdateObj,
            userCompleteHistory,"update-working-memory")
        }
        state=updateState(state,stateUpdateObj)
        console.log(`state updated to:`,state)
        saveStateToStateWithUser(state,stateWithUser)
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
        current_goal:"",
        rough_plan_to_reach_goal:[],
        variables:[],
        env_state:[],
        episodic_memory_descriptions:[],
        current_function_to_execuete:{
            function_name:"",
            inputs:{}
        },
        things_to_note:[],
        final_goal_completed:"no"
    }
    return state
}
function isListFieldType(x: string): x is CustomTypes.listFieldType {
  return CustomTypes.listFieldValues.includes(x as CustomTypes.listFieldType);
}
function isStringFieldType(x: string): x is CustomTypes.listFieldType {
  return CustomTypes.stringFieldValues.includes(x as CustomTypes.stringFieldType);
}
function isObjectFieldType(x: string): x is CustomTypes.objectFieldType {
    return CustomTypes.objectFieldValues.includes(x as CustomTypes.objectFieldType)
}
//to complete
function updateState(state:CustomTypes.workingMemorySchemaType,state_updation_object:CustomTypes.stateUpdationType[]){
    for(let upd of state_updation_object){
        if(upd.type=="delete"){
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
            else if(isObjectFieldType(upd.field)){
                //@ts-ignore
                state[upd.field]={
                    function_name:"",
                    inputs:{}
                }
            }
        }
        else if(upd.type=="add"){
            if(isListFieldType(upd.field)){
                const arr=state[upd.field]
                if(!Array.isArray(arr)){
                    throw new Error(`Field ${upd.field} is not an array`)
                }
                console.log(`upd.updated:`,upd.updated)
                //@ts-ignore
                arr.push(upd.updated)
            }
            else if(isStringFieldType(upd.field)){
                //@ts-ignore
                state[upd.field] = upd.updated
            }
            else if(isObjectFieldType(upd.field)){
                //@ts-ignore
                state[upd.field]=upd.updated
            }
        }
        else if(upd.type=="update"){
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
            else if(isObjectFieldType(upd.field)){
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