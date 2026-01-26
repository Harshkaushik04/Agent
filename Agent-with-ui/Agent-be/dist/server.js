var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
/*old server.ts which was according to this plan is saved in prompts/extras/old_server.txt
generate_working_memory-> reasoning->execuete->interpret-output->update-working-memory->back to reasoning
<also a loop in execuete+interpret-output steps based on "satisfied" field

new plan:
generate_working_memory -> reasoning -> execuete(running+ then llm)[this step can run multiple times
without intervention of reasoning based on instruction of llm("satisifaction of llm")] -> go back to reasoning
*/
import { connectDB, HistoryModel, UserModel, CompleteHistoryModel, WorkingMemoryModel } from "./db.js";
import express from "express";
import cors from "cors";
import jwt from "jsonwebtoken";
import dotenv from "dotenv";
import axios from "axios";
import { WebSocketServer } from "ws";
import * as CustomTypes from './types.js';
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
function requestApprovalStateAndUpdation(ws, username, state, stateUpdationObject, role) {
    return __awaiter(this, void 0, void 0, function* () {
        // const state_string=JSON.stringify(state)
        // const state_updation_string=JSON.stringify(stateUpdationObject)
        console.log(`[requestApprovalStateAndUpdation] sending approval message to frontend`);
        let message = isStateUpdationValid(stateUpdationObject);
        try {
            ws.send(JSON.stringify({
                eventType: "approval",
                state: state,
                stateUpdationObject: stateUpdationObject,
                message: message,
                role: role
            }));
        }
        catch (e) {
            console.log(`Error:${e}`);
        }
        return new Promise((resolve) => {
            pendingApprovals.set(username, resolve);
        });
    });
}
function updateCompleteHistoryWithOnlyStateUpdationObjectAndRequestApprovalStateAndUpdation(ws, username, state, stateUpdationObject, userCompleteHistory, role) {
    return __awaiter(this, void 0, void 0, function* () {
        console.log(`[send-message][updateCompleteHistoryWithOnlyStateUpdationObjectAndRequestApprovalStateAndUpdation]
        stateUpdationObject:`, stateUpdationObject);
        //==========================================
        userCompleteHistory.messages.push({
            role: role,
            content: JSON.stringify(stateUpdationObject),
            messageType: "approvalPending",
            timestamp: new Date()
        });
        yield userCompleteHistory.save();
        //==========================================
        yield requestApprovalStateAndUpdation(ws, username, state, stateUpdationObject, role);
        //==========================================
        if (approved) {
            let temp_len = userCompleteHistory.messages.length;
            userCompleteHistory.messages[temp_len - 1].messageType = "approvalYes";
            yield userCompleteHistory.save();
        }
        else {
            let temp_len = userCompleteHistory.messages.length;
            userCompleteHistory.messages[temp_len - 1].messageType = "approvalNo";
            yield userCompleteHistory.save();
        }
        //==========================================
    });
}
function updateCompleteHistoryWithStateUpdationObjectAndLogAndRequestApprovalStateAndUpdation(ws, username, state, stateUpdationObject, logs, userCompleteHistory, role) {
    return __awaiter(this, void 0, void 0, function* () {
        //==========================================
        let content = JSON.stringify(stateUpdationObject) + "\n" + "logs: " + JSON.stringify(logs);
        userCompleteHistory.messages.push({
            role: role,
            content: content,
            messageType: "approvalPending",
            timestamp: new Date()
        });
        yield userCompleteHistory.save();
        //==========================================
        yield requestApprovalStateAndUpdation(ws, username, state, stateUpdationObject, role);
        //==========================================
        if (approved) {
            let temp_len = userCompleteHistory.messages.length;
            userCompleteHistory.messages[temp_len - 1].messageType = "approvalYes";
            yield userCompleteHistory.save();
        }
        else {
            let temp_len = userCompleteHistory.messages.length;
            userCompleteHistory.messages[temp_len - 1].messageType = "approvalNo";
            yield userCompleteHistory.save();
        }
        //==========================================
    });
}
function requestApprovalState(ws, username, state) {
    return __awaiter(this, void 0, void 0, function* () {
        // const state_string=JSON.stringify(state)
        // const state_updation_string=JSON.stringify(stateUpdationObject)
        ws.send(JSON.stringify({
            eventType: "approval",
            state: state
        }));
        return new Promise((resolve) => {
            pendingApprovals.set(username, resolve);
        });
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
function stateWithUserToState(stateWithUser) {
    var _a, _b;
    // Helper to convert Mongoose Maps to plain Objects (fixes "inputs: {}" bug)
    const mapToObject = (map) => {
        if (map instanceof Map)
            return Object.fromEntries(map);
        if (typeof map === 'object' && map !== null)
            return map;
        return {};
    };
    let state = {
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
            inputs: mapToObject(plan.inputs), // Convert Map -> Object
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
            function_name: ((_a = stateWithUser.current_function_to_execuete) === null || _a === void 0 ? void 0 : _a.function_name) || "",
            inputs: mapToObject((_b = stateWithUser.current_function_to_execuete) === null || _b === void 0 ? void 0 : _b.inputs)
        }
    };
    return state;
}
function saveStateToStateWithUser(state, stateWithUser) {
    return __awaiter(this, void 0, void 0, function* () {
        stateWithUser.chat_history = state.chat_history;
        stateWithUser.previous_actions_and_logs = state.previous_actions_and_logs;
        stateWithUser.final_goal = state.final_goal;
        stateWithUser.current_goal = state.current_goal;
        stateWithUser.rough_plan_to_reach_goal = state.rough_plan_to_reach_goal;
        stateWithUser.variables = state.variables;
        stateWithUser.env_state = state.env_state;
        stateWithUser.episodic_memory_descriptions = state.episodic_memory_descriptions;
        stateWithUser.current_function_to_execuete = state.current_function_to_execuete;
        stateWithUser.things_to_note = state.things_to_note;
        stateWithUser.final_goal_completed = state.final_goal_completed;
        yield stateWithUser.save();
    });
}
/*
  Helper to check if an object has EXACTLY the expected keys (no more, no less).
 */
function hasExactKeys(obj, requiredKeys) {
    if (!obj || typeof obj !== 'object')
        return false;
    const objKeys = Object.keys(obj);
    // 1. Check for missing keys
    const missing = requiredKeys.filter(k => !objKeys.includes(k));
    if (missing.length > 0) {
        return false;
    }
    // 2. Check for extra keys
    const extra = objKeys.filter(k => !requiredKeys.includes(k));
    if (extra.length > 0) {
        return false;
    }
    return true;
}
const CHAT_HISTORY_KEYS = ["serial_number", "role", "content"];
const ADD_PREVIOUS_ACTIONS_AND_LOGS_KEYS = ["serial_number",
    "description", "function_name", "inputs", "outputs", "log", "filter_words"];
const ROUGH_PLAN_TO_REACH_GOAL_KEYS = ["serial_number",
    "description", "function_name", "inputs", "brief_expected_outputs", "status"
];
const VARIABLES_KEYS = ["serial_number", "variable_type",
    "description", "content", "filter_words"
];
const ENV_STATE_KEYS = ["serial_number", "description", "content"];
const EPISODIC_MEMORY_DESCRIPTIONS_KEYS = ["serial_number", "description"];
const CURRENT_FUNCTION_TO_EXECUETE_KEYS = ["function_name", "inputs"];
const THINGS_TO_NOTE_KEYS = ["serial_number", "description", "content"];
/*
 Main Validator Function
 */
export function isStateUpdationValid(updates) {
    console.log(`[send-message][isStateUpdationValid] stateUpdationObject:`, updates);
    if (!Array.isArray(updates))
        return "stateUpdationObject isnt list";
    for (const update of updates) {
        if (hasExactKeys(update, ["type", "field", "serial_number"])) { // type==delete
            continue;
        }
        else if (hasExactKeys(update, ["type", "field", "serial_number", "updated"])) { // type== update or add
            if (update.field == "satisfied" || update.field == "final_goal" || update.field == "current_goal" || update.field == "final_goal_completed") {
                if (typeof update.updated !== "string")
                    return "updated field for satisfied/final_goal/current_goal should be string";
            }
            else if (update.field == "chat_history") {
                if (!hasExactKeys(update.updated, CHAT_HISTORY_KEYS))
                    return "chat_history updated field isnt correct";
            }
            else if (update.field == "previous_actions_and_logs") {
                if (!hasExactKeys(update.updated, ADD_PREVIOUS_ACTIONS_AND_LOGS_KEYS))
                    return "previous_actions_and_logs updated field isnt correct";
            }
            else if (update.field == "rough_plan_to_reach_goal") {
                if (!hasExactKeys(update.updated, ROUGH_PLAN_TO_REACH_GOAL_KEYS))
                    return "rough_plan_to_reach_goal updated field isnt correct";
            }
            else if (update.field == "variables") {
                if (!hasExactKeys(update.updated, VARIABLES_KEYS))
                    return "variables updated field isnt correct";
            }
            else if (update.field == "env_state") {
                if (!hasExactKeys(update.updated, ENV_STATE_KEYS))
                    return "env_state updated field isnt correct";
            }
            else if (update.field == "episodic_memory_descriptions") {
                if (!hasExactKeys(update.updated, EPISODIC_MEMORY_DESCRIPTIONS_KEYS))
                    return "episodic_memory_descriptions updated field isnt correct";
            }
            else if (update.field == "things_to_note") {
                if (!hasExactKeys(update.updated, THINGS_TO_NOTE_KEYS))
                    return "things_to_note updated field isnt correct";
            }
            else {
                return "field isnt correct";
            }
        }
        else {
            return "state updation object should have either\n:{type,field,serial_number} or {type,field,serial_number,updated}";
        }
    }
    return "correct";
}
// function sendOutput(ws:WebSocket,username:string)
let approved = false;
let feedback = "";
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
        usernameToWebSocket.set(username, ws);
        webSocketToUsername.set(ws, username);
        if (json_message.eventType == "approval") {
            const resolve = pendingApprovals.get(username);
            //since user can disconnect and then reconnect, this would throw error at server, so not good
            // if(!resolve){
            //     throw new Error(`[server.ts] No pending approvals from username ${username}`)
            // }
            if (json_message.approval == "yes") {
                approved = true;
            }
            else {
                approved = false;
                feedback = (json_message === null || json_message === void 0 ? void 0 : json_message.feedback) ? json_message.feedback : "";
            }
            if (resolve) {
                resolve(json_message.approval == "yes");
                pendingApprovals.delete(username);
            }
        }
    });
});
app.use(express.json());
// app.use(cors({
//     "origin":"http://localhost:5173"
// }));
app.use(cors());
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
    yield CompleteHistoryModel.create({
        username: username,
        model: model,
        title: `title${num_chats + 1}`
    });
    yield WorkingMemoryModel.create({
        username: username,
        model: model,
        title: `title${num_chats + 1}`,
        chat_history: [],
        previous_actions_and_logs: [],
        final_goal: "",
        current_goal: "",
        rough_plan_to_reach_goal: [],
        variables: [],
        env_state: [],
        episodic_memory_descriptions: [],
        current_function_to_execuete: {
            function_name: "",
            inputs: {}
        },
        things_to_note: [],
        final_goal_completed: "yes"
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
    let user = yield CompleteHistoryModel.findOne({
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
    let user = yield CompleteHistoryModel.findOne({
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
    yield CompleteHistoryModel.deleteOne({
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
    let stateWithUser = yield WorkingMemoryModel.findOne({
        username: username,
        model: model,
        title: `title${chat_number}`
    });
    let state;
    if (!stateWithUser) {
        console.log("why is stateWithUser not defined till now?");
        yield WorkingMemoryModel.create({
            username: username,
            model: model,
            title: `title${chat_number}`,
            chat_history: [{
                    serial_number: 0,
                    role: "user",
                    content: user_message
                }],
            previous_actions_and_logs: [],
            final_goal: user_message,
            current_goal: "",
            rough_plan_to_reach_goal: [],
            variables: [],
            env_state: [],
            episodic_memory_descriptions: [],
            current_function_to_execuete: {
                function_name: "",
                inputs: {}
            },
            things_to_note: [],
            final_goal_completed: "no"
        });
        stateWithUser = yield WorkingMemoryModel.findOne({
            username: username,
            model: model,
            title: `title${chat_number}`
        });
        if (!stateWithUser) {
            throw new Error("why is stateWithUser still not defined??");
        }
        state = stateWithUserToState(stateWithUser);
    }
    else {
        state = stateWithUserToState(stateWithUser);
        let len_chat = state.chat_history.length;
        let serial_num = 1;
        if (len_chat != 0) {
            serial_num = state.chat_history[len_chat - 1].serial_number + 1;
        }
        state.chat_history.push({
            serial_number: serial_num,
            role: "user",
            content: user_message
        });
        saveStateToStateWithUser(state, stateWithUser);
    }
    let userCompleteHistory = yield CompleteHistoryModel.findOne({
        username: username,
        model: model,
        title: `title${chat_number}`
    });
    if (!userCompleteHistory) {
        yield CompleteHistoryModel.create({
            username: username,
            model: model,
            title: `title${chat_number}`,
            messages: [{
                    role: "user",
                    content: user_message,
                    messageType: "normal",
                    timestamp: new Date()
                }]
        });
        userCompleteHistory = yield CompleteHistoryModel.findOne({
            username: username,
            model: model,
            title: `title${chat_number}`
        });
        if (!userCompleteHistory) {
            throw new Error("entry just made, so this error is technically not possible");
        }
    }
    else {
        userCompleteHistory.messages.push({
            role: "user",
            content: user_message,
            messageType: "normal",
            timestamp: new Date()
        });
        yield userCompleteHistory.save();
    }
    const userHistory = yield HistoryModel.findOne({
        username: username,
        model: model,
        title: `title${chat_number}`
    });
    if (!userHistory) {
        throw new Error("why is userHistory not defined");
    }
    userHistory.messages.push({
        role: "user",
        content: user_message,
        before_think: "",
        after_think: "",
        timestamp: new Date()
    });
    yield userHistory.save();
    const foundWs = usernameToWebSocket.get(username);
    if (!foundWs) {
        throw new Error("[server.ts] websocket not connected till now!! => connect message not received?");
    }
    //to complete: implementation of feedback,approval by user
    let resp;
    let stateUpdateObj = [];
    feedback = "";
    approved = false;
    let satisfied = "yes";
    while (!approved) {
        // console.log("request:")
        // console.log("state:",state)
        // console.log("feedback:",feedback)
        // console.log("model:",model)
        // console.log("chat_number:",chat_number)
        resp = yield axios.post("http://localhost:5000/generate-working-memory", {
            state: state,
            feedback: feedback,
            model: model,
            chat_number: chat_number
        });
        stateUpdateObj = resp.data.stateUpdationObject;
        yield updateCompleteHistoryWithOnlyStateUpdationObjectAndRequestApprovalStateAndUpdation(foundWs, username, state, stateUpdateObj, userCompleteHistory, "generate-working-memory");
    }
    console.log(`stateUpdateObj:`, stateUpdateObj);
    console.log(`old state:`, state);
    let result = updateState(state, stateUpdateObj, satisfied);
    state = result.state;
    satisfied = result.satisfied;
    console.log(`state updated to:`, state);
    saveStateToStateWithUser(state, stateWithUser);
    let logs = [];
    while (state.final_goal_completed != "yes") {
        feedback = "";
        approved = false;
        satisfied = "yes";
        while (!approved) {
            let resp1 = yield axios.post("http://localhost:5000/reasoning", {
                state: state,
                feedback: feedback,
                model: model,
                chat_number: chat_number
            });
            stateUpdateObj = resp1.data.stateUpdationObject;
            yield updateCompleteHistoryWithOnlyStateUpdationObjectAndRequestApprovalStateAndUpdation(foundWs, username, state, stateUpdateObj, userCompleteHistory, "reasoning");
        }
        result = updateState(state, stateUpdateObj, satisfied);
        state = result.state;
        satisfied = result.satisfied;
        console.log(`state updated to:`, state);
        saveStateToStateWithUser(state, stateWithUser);
        while (satisfied != "yes") {
            approved = false;
            feedback = "";
            while (!approved) {
                let resp2 = yield axios.post("http://localhost:5000/execuete", {
                    state: state,
                    model: model,
                    chat_number: chat_number,
                    feedback: feedback
                });
                logs = resp2.data.logs;
                stateUpdateObj = resp2.data.stateUpdationObject;
                yield updateCompleteHistoryWithStateUpdationObjectAndLogAndRequestApprovalStateAndUpdation(foundWs, username, state, stateUpdateObj, logs, userCompleteHistory, "execuete");
            }
            result = updateState(state, stateUpdateObj, satisfied);
            state = result.state;
            satisfied = result.satisfied;
            console.log(`state updated to:`, state);
            saveStateToStateWithUser(state, stateWithUser);
        }
    }
    //generate-working-memory
    //while-loop-start{
    //reasoning
    //execuete
    //interpret-output
    //update-working-memory
    //while-loop-end}
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
        current_goal: "",
        rough_plan_to_reach_goal: [],
        variables: [],
        env_state: [],
        episodic_memory_descriptions: [],
        current_function_to_execuete: {
            function_name: "",
            inputs: {}
        },
        things_to_note: [],
        final_goal_completed: "no"
    };
    return state;
}
function isListFieldType(x) {
    return CustomTypes.listFieldValues.includes(x);
}
function isStringFieldType(x) {
    return CustomTypes.stringFieldValues.includes(x);
}
function isObjectFieldType(x) {
    return CustomTypes.objectFieldValues.includes(x);
}
//to complete
function updateState(state, state_updation_object, satisfied) {
    for (let upd of state_updation_object) {
        if (upd.type == "delete") {
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
            else if (isObjectFieldType(upd.field)) {
                //@ts-ignore
                state[upd.field] = {
                    function_name: "",
                    inputs: {}
                };
            }
        }
        else if (upd.type == "add") {
            if (isListFieldType(upd.field)) {
                const arr = state[upd.field];
                if (!Array.isArray(arr)) {
                    throw new Error(`Field ${upd.field} is not an array`);
                }
                console.log(`upd.updated:`, upd.updated);
                //@ts-ignore
                arr.push(upd.updated);
            }
            else if (isStringFieldType(upd.field)) {
                //@ts-ignore
                state[upd.field] = upd.updated;
            }
            else if (isObjectFieldType(upd.field)) {
                //@ts-ignore
                state[upd.field] = upd.updated;
            }
            else if (upd.field == "satisfied") {
                satisfied = upd.updated;
            }
        }
        else if (upd.type == "update") {
            if (isListFieldType(upd.field)) {
                const arr = state[upd.field];
                if (!Array.isArray(arr)) {
                    throw new Error(`Field ${upd.field} is not an array`);
                }
                //@ts-ignore
                arr[upd.serial_number] = upd.updated;
            }
            else if (isStringFieldType(upd.field)) {
                //@ts-ignore
                state[upd.field] = upd.updated;
            }
            else if (isObjectFieldType(upd.field)) {
                //@ts-ignore
                state[upd.field] = upd.updated;
            }
        }
    }
    return {
        state: state,
        satisfied: satisfied
    };
}
app.listen(PORT, () => {
    console.log(`server listening at port ${PORT}`);
});
