import { connectDB, HistoryModel, UserModel } from "./db.js"
import { Request, Response, NextFunction } from 'express';
import express from "express";
import cors from "cors";
import jwt from "jsonwebtoken";
import dotenv from "dotenv";
import axios from "axios"
import WebSocket,{WebSocketServer} from "ws";
import * as CustomTypes from './types.js'

const wss=new WebSocketServer({port:8080})
let usernameToWebSocket=new Map<string,WebSocket>()
let webSocketToUsername=new Map<WebSocket,string>()
dotenv.config();
connectDB();
let app=express();

const JWT_SECRET="randomnum1";
const PORT=3000;

let pendingApprovals=new Map<string,(choice:boolean)=>void>
async function requestApproval(ws: WebSocket, username: string, message:string): Promise<boolean> {
    ws.send(JSON.stringify({
        eventType: "approval",
        message:message
    }));
    return new Promise((resolve) => {
        pendingApprovals.set(username, resolve);
    });
}

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
            resolve(json_message.message=="yes")
            pendingApprovals.delete(username)
        }
    })
})

app.use(express.json());
app.use(cors({
    "origin":"http://localhost:5173"
}));

function authMiddleware(req:Request,res:Response,next:NextFunction){
    const custom_req=req as CustomTypes.afterLoginRequest
    const custom_res=res as Response<CustomTypes.anyResponseType>
    if(!custom_req.headers.token){
        return custom_res.json({
            valid:false
        });
    }
    else{
        try {
            const decryptedData = jwt.verify(custom_req.headers.token as string, JWT_SECRET) as CustomTypes.jwtDecrypted;
            req.body.decrypted_username = decryptedData.username; 
            next();
        } catch (err) {
            return custom_res.json({
                valid:false
            });
        }
    }
}

app.post("/signup",async (req:CustomTypes.signUpRequest,res:Response<CustomTypes.signUpType>)=>{
    let username=req.body.username;
    let password=req.body.password;
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
    let username=req.body.username;
    let password=req.body.password;
    let user=await UserModel.findOne({
        username:username,
        password:password
    });
    if(!user) {return res.json({
        valid:false
    })}
    // PROXY_MODEL,username,PROXY_TITLE---->num_chats already created
    let chat_row=await HistoryModel.findOne({
        username:username,
        model:process.env.PROXY_MODEL,
        title:process.env.PROXY_TITLE
    })
    if(!chat_row){
        throw new Error("chat number row in HistoryModel does not exist")
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
    const custom_res=res as Response<CustomTypes.loadHistoryTitlesType>
    const custom_req=req as CustomTypes.loadHistoryTitlesRequest
    let username=custom_req.body.decrypted_username;
    let model=custom_req.body.model;
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
    return custom_res.json({
        valid:true,
        titles:titlesList
    })
})

app.post("/load-new-chat",async (req:Request,res:Response)=>{
    console.log(`[load-new-chat] request recieved`)
    const custom_req=req as CustomTypes.loadNewChatRequest
    const custom_res=res as Response<CustomTypes.loadNewChatType>
    let username=custom_req.body.decrypted_username;
    let model=custom_req.body.model;
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
    return custom_res.json({
        valid:true,
        chat_number:num_chats+1
    })
})

app.get("/update-chat",async (req:Request,res:Response)=>{
    console.log(`[update-chat] entered request`)
    const custom_req=req as CustomTypes.updateChatRequest
    const custom_res=res as Response<CustomTypes.updateChatType>
    let username=custom_req.body.decrypted_username;
    let model=custom_req.headers.model;
    let chat_number=custom_req.headers.chat_number;
    let user=await HistoryModel.findOne({
        username:username,
        model:model,
        title:`title${chat_number}`
    })
    console.log(`[update-chat] username:${username},model:${model},title:title${chat_number}`)
    return custom_res.json({
        valid:true,
        value_json:(user?.messages ? user.messages : [])
    })
})

app.get("/click-history",async (req:Request,res:Response)=>{
    console.log(`[click-history] entered request`)
    const custom_req=req as CustomTypes.clickHistoryRequest
    const custom_res=res as Response<CustomTypes.clickHistoryType>
    let username=custom_req.body.decrypted_username;
    let model=custom_req.headers.model;
    let chat_number=custom_req.headers.chat_number;
    console.log(`[click-history]username:${username} model:${model} title:title${chat_number}`)
    let user=await HistoryModel.findOne({
        username:username,
        model:model,
        title:`title${chat_number}`
    })
    console.log(`user.messages:${user?.messages}`)
    return custom_res.json({
        valid:true,
        value_json:(user?.messages ? user.messages:[])
    })
})

app.delete("/delete-chat",async (req:Request,res:Response)=>{
    console.log(`[delete-chat] entered request`)
    const custom_req=req as CustomTypes.deleteChatRequest
    const custom_res=res as Response<CustomTypes.deleteChatType>
    let username=custom_req.body.decrypted_username;
    let model=custom_req.headers.model;
    let chat_number=custom_req.headers.chat_number;
    await HistoryModel.deleteOne({
        username:username,
        model:model,
        title:`title${chat_number}`
    })
    return custom_res.json({
        valid:true,
        chat_number:-1
    })
})

app.post("/send-message",async (req:Request,res:Response)=>{
    console.log(`[send-message]request arrived`)
    const custom_req=req as CustomTypes.sendMessageRequest
    const custom_res=res as Response<CustomTypes.sendMessageType>
    let username=custom_req.body.decrypted_username;
    let user_message=custom_req.body.message;
    let model=custom_req.body.model;
    let chat_number=custom_req.body.chat_number;
    const resp=await axios.post<CustomTypes.generateModelType>("http://localhost:5000/generate-model",{

    })
    // await runPython(username,model,chat_number,user_message);
    return custom_res.json({
        valid:true
    })
})

function initialiseWorkingMemory(){

}

app.listen(PORT,()=>{
    console.log(`server listening at port ${PORT}`)
})