import { connectDB, HistoryModel, UserModel } from "./db.js";
import express from "express";
import cors from "cors";
import jwt from "jsonwebtoken";
import dotenv from "dotenv";
import { spawn } from "child_process";
import path from "path";
dotenv.config();
connectDB();
let app=express();

const JWT_SECRET="randomnum1";
const PORT=3000;
app.use(express.json());
app.use(cors({
    "origin":"http://localhost:5173"
}));

function authMiddleware(req,res,next){
    if(!req.headers.token){
        return res.json({
            valid:false
        });
    }
    else{
        try {
            const decryptedData = jwt.verify(req.headers.token, JWT_SECRET);
            req.username = decryptedData.username; 
            next();
        } catch (err) {
            return res.json({
                valid:false
            });
        }
    }
}
async function runPython(username,model,chat_number,user_message){
    let response={};
    const PythonPromise=new Promise((resolve,reject)=>{
        console.log("[runPython function] entered pythonPromise")
        const py=spawn("python3",["-u",
            "-W","ignore",
            "run_model.py",
            "--username",JSON.stringify(username),
            "--model",JSON.stringify(model),
            "--chat_number",JSON.stringify(chat_number),
            "--user_message",JSON.stringify(user_message)]);
        py.stdout.on("data", (data) => {
            // console.log(data.toString());
            process.stdout.write(data.toString());
        });
        py.stderr.on("data",(data)=>{
            response.error=data.toString();
            console.error(`[PYTHON ERROR]: ${data.toString()}`);
        })
        py.on("close",(code)=>{
            if(code!==0){
                response.error="Python crashed!";
            }
            else resolve()
        })
    })
    await PythonPromise;
    let raw_output="";
}

app.post("/signup",async (req,res)=>{
    let username=req.body.username;
    let password=req.body.password;
    let user=await UserModel.findOne({
        username:username
    })
    if(user){
        res.json({
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
    res.json({
        whetherDuplicate:false
    })
})

app.post("/login",async (req,res)=>{
    let username=req.body.username;
    let password=req.body.password;
    let user=await UserModel.findOne({
        username:username,
        password:password
    });
    if(!user) {res.json({
        valid:false
    })}
    // PROXY_MODEL,username,PROXY_TITLE---->num_chats already created
    let chat_row=await HistoryModel.findOne({
        username:username,
        model:process.env.PROXY_MODEL,
        title:process.env.PROXY_TITLE
    })
    let num_chats=0;
    num_chats=Number(chat_row.messages[0].content);
    chat_row.messages[0].content = String(num_chats + 1);
    await chat_row.save();
    if(user){
        let jwt_token=jwt.sign({
            "username":username
        },JWT_SECRET);
        res.json({
            username:username,
            token:jwt_token,
            valid:true
        })
    }
})

app.use(authMiddleware);
app.post("/load-history-titles",async (req,res)=>{
    let username=req.username;
    let model=req.body.model;
    let historyTitles=await HistoryModel.find({
        username:username,
        model:model
    },"title");
    let len=historyTitles.length;
    let titlesList=[]
    for(let i=0;i<len;i++){
        titlesList.push(historyTitles[i]["title"]);
    }
    res.json({
        valid:true,
        titles:titlesList
    })
})

app.post("/load-new-chat",async (req,res)=>{
    console.log(`[load-new-chat] request recieved`)
    let username=req.username;
    let model=req.body.model;
    // PROXY_MODEL,username,PROXY_TITLE---->num_chats already created
    let chat_row=await HistoryModel.findOne({
        username:username,
        model:process.env.PROXY_MODEL,
        title:process.env.PROXY_TITLE
    })
    let num_chats=Number(chat_row.messages[0].content);
    await HistoryModel.create({
        username:username,
        model:model,
        title:`title${num_chats+1}`
    })
    chat_row.messages[0].content = String(num_chats + 1);
    console.log(`[load-new-chat] chat_row.messages[0].content:${chat_row.messages[0].content}`)
    await chat_row.save();
    res.json({
        valid:true,
        chat_number:num_chats+1
    })
})

app.post("/send-message",async (req,res)=>{
    console.log(`[send-message]request arrived`)
    let username=req.username;
    let user_message=req.body.message;
    let model=req.body.model;
    let chat_number=req.body.chat_number;
    await runPython(username,model,chat_number,user_message);
    res.json({
        valid:true
    })
})

app.get("/update-chat",async (req,res)=>{
    console.log(`[update-chat] entered request`)
    let username=req.username;
    let model=req.headers.model;
    let chat_number=req.headers.chat_number;
    let user=await HistoryModel.findOne({
        username:username,
        model:model,
        title:`title${chat_number}`
    })
    console.log(`[update-chat] username:${username},model:${model},title:title${chat_number}`)
    res.json({
        valid:true,
        value_json:(user?.messages ? user.messages : [])
    })
})

app.get("/click-history",async (req,res)=>{
    console.log(`[click-history] entered request`)
    let username=req.username;
    let model=req.headers.model;
    let chat_number=req.headers.chat_number;
    console.log(`[click-history]username:${username} model:${model} title:title${chat_number}`)
    let user=await HistoryModel.findOne({
        username:username,
        model:model,
        title:`title${chat_number}`
    })
    console.log(`user.messages:${user.messages}`)
    res.json({
        valid:true,
        value_json:(user?.messages ? user.messages:[])
    })
})

app.delete("/delete-chat",async (req,res)=>{
    console.log(`[delete-chat] entered request`)
    let username=req.username;
    let model=req.headers.model;
    let chat_number=req.headers.chat_number;
    await HistoryModel.deleteOne({
        username:username,
        model:model,
        title:`title${chat_number}`
    })
    res.json({
        valid:true,
        chat_number:-1
    })
})

app.listen(PORT,()=>{
    console.log(`server listening at port ${PORT}`)
})