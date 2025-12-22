var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
import { connectDB, HistoryModel, UserModel } from "./db.js";
import express from "express";
import cors from "cors";
import jwt from "jsonwebtoken";
import dotenv from "dotenv";
import axios from "axios";
import { WebSocketServer } from "ws";
import path from 'path';
import { fileURLToPath } from "url";
const wss = new WebSocketServer({ port: 8080 });
let usernameToWebSocket = new Map();
let webSocketToUsername = new Map();
// Recreate __dirname for ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, '../../.env') });
// Now your existing line will work
// console.log(`dotenv location:${path.resolve(__dirname, '../../.env')}`)
connectDB();
let app = express();
const JWT_SECRET = "randomnum1";
const PORT = 3000;
let pendingApprovals = new Map;
function requestApproval(ws, username, message) {
    return __awaiter(this, void 0, void 0, function* () {
        ws.send(JSON.stringify({
            eventType: "approval",
            message: message
        }));
        return new Promise((resolve) => {
            pendingApprovals.set(username, resolve);
        });
    });
}
wss.on("connection", function (ws) {
    console.log("new user connected");
    ws.on("message", (msg) => {
        const json_message = JSON.parse(msg.toString());
        let decryptedData;
        try {
            decryptedData = jwt.verify(json_message.token, JWT_SECRET);
        }
        catch (err) {
            throw new Error("[server.ts]WebSocket Check: wrong jwt token");
        }
        const username = decryptedData.username;
        if (!usernameToWebSocket.get(username)) {
            console.log(`username:${username} websocket registered`);
            usernameToWebSocket.set(username, ws);
            webSocketToUsername.set(ws, username);
        }
        if (json_message.eventType == "approval") {
            const resolve = pendingApprovals.get(username);
            if (!resolve) {
                throw new Error(`[server.ts] No pending approvals from username ${username}`);
            }
            resolve(json_message.message == "yes");
            pendingApprovals.delete(username);
        }
    });
});
app.use(express.json());
app.use(cors({
    "origin": "http://localhost:5173"
}));
function authMiddleware(req, res, next) {
    // const custom_req=req as CustomTypes.afterLoginRequest
    // const custom_res=res as Response<CustomTypes.anyResponseType>
    if (!req.headers.token) {
        console.log(`hi:`, req.headers.token);
        return res.json({
            valid: false
        });
    }
    else {
        try {
            const rawDecryptedData = jwt.verify(req.headers.token, JWT_SECRET);
            const decryptedData = rawDecryptedData;
            //@ts-ignore
            req.decrypted_username = decryptedData.username;
            //@ts-ignore
            console.log(`req.decrypted_username:`, req.decrypted_username);
            next();
        }
        catch (err) {
            console.log("err:", err);
            console.log(`hi2`);
            return res.json({
                valid: false
            });
        }
    }
}
app.post("/signup", (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    let username = req.body.username;
    let password = req.body.password;
    let user = yield UserModel.findOne({
        username: username
    });
    if (user) {
        return res.json({
            whetherDuplicate: true
        });
    }
    // PROXY_MODEL,username,PROXY_TITLE---->num_chats already created
    yield HistoryModel.create({
        username: username,
        model: process.env.PROXY_MODEL,
        title: process.env.PROXY_TITLE,
        messages: [{ "role": "system", "content": "0" }]
    });
    //username not taken=>make new id
    yield UserModel.create({
        username: username,
        password: password
    });
    return res.json({
        whetherDuplicate: false
    });
}));
app.post("/login", (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    let username = req.body.username;
    let password = req.body.password;
    let user = yield UserModel.findOne({
        username: username,
        password: password
    });
    if (!user) {
        return res.json({
            valid: false
        });
    }
    // PROXY_MODEL,username,PROXY_TITLE---->num_chats already created
    console.log(`title:${process.env.PROXY_TITLE}`);
    let chat_row = yield HistoryModel.findOne({
        username: username,
        model: process.env.PROXY_MODEL,
        title: process.env.PROXY_TITLE
    });
    if (!chat_row) {
        throw new Error("[server.ts] chat number row in HistoryModel does not exist");
    }
    let num_chats = 0;
    num_chats = Number(chat_row.messages[0].content);
    chat_row.messages[0].content = String(num_chats + 1);
    yield chat_row.save();
    if (user) {
        let jwt_token = jwt.sign({
            "username": username
        }, JWT_SECRET);
        return res.json({
            username: username,
            token: jwt_token,
            valid: true
        });
    }
}));
app.use(authMiddleware);
app.post("/load-history-titles", (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    // const custom_res=res as Response<CustomTypes.loadHistoryTitlesType>
    // const custom_req=req as CustomTypes.loadHistoryTitlesRequest
    //@ts-ignore
    let username = req.decrypted_username;
    let model = req.body.model;
    let historyTitles = yield HistoryModel.find({
        username: username,
        model: model
    }, "title");
    let len = historyTitles.length;
    let titlesList = [];
    for (let i = 0; i < len; i++) {
        let custom_title = historyTitles[i]["title"];
        if (!custom_title) {
            throw new Error("historyTitles[i]['title'] doesnt exist");
        }
        titlesList.push(custom_title);
    }
    return res.json({
        valid: true,
        titles: titlesList
    });
}));
app.post("/load-new-chat", (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    console.log(`[load-new-chat] request recieved`);
    // const custom_req=req as CustomTypes.loadNewChatRequest
    // const custom_res=res as Response<CustomTypes.loadNewChatType>
    //@ts-ignore
    let username = req.decrypted_username;
    let model = req.body.model;
    // PROXY_MODEL,username,PROXY_TITLE---->num_chats already created
    let chat_row = yield HistoryModel.findOne({
        username: username,
        model: process.env.PROXY_MODEL,
        title: process.env.PROXY_TITLE
    });
    if (!chat_row) {
        throw new Error("chat number row in HistoryModel does not exist");
    }
    let num_chats = Number(chat_row.messages[0].content);
    yield HistoryModel.create({
        username: username,
        model: model,
        title: `title${num_chats + 1}`
    });
    chat_row.messages[0].content = String(num_chats + 1);
    console.log(`[load-new-chat] chat_row.messages[0].content:${chat_row.messages[0].content}`);
    yield chat_row.save();
    return res.json({
        valid: true,
        chat_number: num_chats + 1
    });
}));
app.get("/update-chat", (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    console.log(`[update-chat] entered request`);
    // const custom_req=req as CustomTypes.updateChatRequest
    // const custom_res=res as Response<CustomTypes.updateChatType>
    //@ts-ignore
    let username = req.decrypted_username;
    let model = String(req.headers.model);
    let chat_number = Number(req.headers.chat_number);
    let user = yield HistoryModel.findOne({
        username: username,
        model: model,
        title: `title${chat_number}`
    });
    console.log(`[update-chat] username:${username},model:${model},title:title${chat_number}`);
    return res.json({
        valid: true,
        value_json: ((user === null || user === void 0 ? void 0 : user.messages) ? user.messages : [])
    });
}));
app.get("/click-history", (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    console.log(`[click-history] entered request`);
    // const custom_req=req as CustomTypes.clickHistoryRequest
    // const custom_res=res as Response<CustomTypes.clickHistoryType>
    //@ts-ignore
    let username = req.decrypted_username;
    let model = String(req.headers.model);
    let chat_number = Number(req.headers.chat_number);
    console.log(`[click-history]username:${username} model:${model} title:title${chat_number}`);
    let user = yield HistoryModel.findOne({
        username: username,
        model: model,
        title: `title${chat_number}`
    });
    console.log(`user.messages:${user === null || user === void 0 ? void 0 : user.messages}`);
    return res.json({
        valid: true,
        value_json: ((user === null || user === void 0 ? void 0 : user.messages) ? user.messages : [])
    });
}));
app.delete("/delete-chat", (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    console.log(`[delete-chat] entered request`);
    // const custom_req=req as CustomTypes.deleteChatRequest
    // const custom_res=res as Response<CustomTypes.deleteChatType>
    //@ts-ignore
    let username = req.decrypted_username;
    let model = String(req.headers.model);
    let chat_number = Number(req.headers.chat_number);
    yield HistoryModel.deleteOne({
        username: username,
        model: model,
        title: `title${chat_number}`
    });
    return res.json({
        valid: true,
        chat_number: -1
    });
}));
app.post("/send-message", (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    console.log(`[send-message]request arrived`);
    // const custom_req=req as CustomTypes.sendMessageRequest
    // const custom_res=res as Response<CustomTypes.sendMessageType>
    //@ts-ignore
    let username = req.decrypted_username;
    let user_message = req.body.message;
    let model = req.body.model;
    let chat_number = Number(req.body.chat_number);
    let state = initialiseWorkingMemory(user_message);
    const foundWs = usernameToWebSocket.get(username);
    if (!foundWs) {
        throw new Error("[server.ts] websocket not connected till now!! => connect message not received?");
    }
    //to complete: implementation of feedback,approval by user
    const resp = yield axios.post("http://localhost:5000/generate-working-memory", {
        state: state
    });
    state = resp.data.state;
    while (!state.final_goal_completed) {
        let resp1 = yield axios.post("http://localhost:5000/reasoning", {
            state: state
        });
        let before_think = resp1.data.before_think;
        let stateUpdateObj = resp1.data.stateUpdationObject;
        updateStateWithBeforeThink(before_think);
        updateState(stateUpdateObj);
        let resp2 = yield axios.post("http://localhost:5000/execuete", {
            state: state,
            model: model,
            chat_number: chat_number
        });
        let log = resp2.data.log;
        stateUpdateObj = resp2.data.stateUpdationObject;
        updateState(stateUpdateObj);
        let resp3 = yield axios.post("http://localhost:5000/make-log", {
            state: state,
            log: log
        });
        stateUpdateObj = resp3.data.stateUpdationObject;
        updateState(stateUpdateObj);
        let resp4 = yield axios.post("http://localhost:5000/update-working-memory", {
            state: state
        });
        stateUpdateObj = resp4.data.stateUpdationObject;
        updateState(stateUpdateObj);
    }
    //generate-working-memory
    //while-loop-start{
    //reasoning
    //execuete
    //make-log
    //update-working-memory
    //while-loop-end}
    // const resp=await axios.post<CustomTypes.generateModelType>("http://localhost:5000/generate-model",{
    // })
    return res.json({
        valid: true
    });
}));
function initialiseWorkingMemory(user_message) {
    const state = {
        chat_history: [{
                serial_number: 0,
                role: "user",
                content: user_message
            }],
        previous_actions_and_logs: [],
        final_goal: user_message,
        current_goal: "reasoning to make a plan",
        rough_plan_to_reach_goal: [],
        summaries: [],
        env_state: [],
        episodic_memory_descriptions: [],
        current_function_to_execute: {
            funcation_name: "",
            inputs: {}
        },
        things_to_note: [],
        final_goal_completed: false
    };
    return state;
}
//to complete
function updateState(state_updation_object) {
}
function updateStateWithBeforeThink(before_think) {
}
app.listen(PORT, () => {
    console.log(`server listening at port ${PORT}`);
});
